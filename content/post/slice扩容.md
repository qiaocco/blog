---
title: "golang slice扩容"
date: 2021-06-25T14:31:39+08:00
draft: true
tags: ["golang"]
---



先看一个例子：

```go
s1 := []int{1, 2}
println(len(s1), cap(s1)) // 2 2

s1 = append(s1, 3, 4, 5)
println(len(s1), cap(s1)) // 5 6，cap从2扩容到6，为什么不是5？
```

# 扩容规则

源码：

```go
// runtime/slice.go
// func growslice(et *_type, old slice, cap int) slice {}

// old.cap 现有容量
// cap 预估容量
// newcap 最终分配的容量
newcap := old.cap
doublecap := newcap + newcap
if cap > doublecap {
    newcap = cap
} else {
    if old.cap < 1024 {
        newcap = doublecap
    } else {
        // Check 0 < newcap to detect overflow
        // and prevent an infinite loop.
        for 0 < newcap && newcap < cap {
            newcap += newcap / 4
        }
        // Set newcap to the requested cap when
        // the newcap calculation overflowed.
        if newcap <= 0 {
            newcap = cap
        }
    }
}

```

扩容规则：

- 现有容量double后，小于预估容量，新容量就等于预估容量
- 现有容量double后，大于预估容量时，
  - 现有容量小于1024，那么新容量就等于现有容量double
  - 现有容量大于1024，新容量等于现有容量*1.25

回到上面的例子中：

// old.cap 现有容量 = 2
// cap 预估容量 = 5
// newcap 新容量 = 5

分析到这一步，新容量应该是5，但是结果是6。

这是为什么呢？

# 内存对齐

  计算出了新容量之后，还没有完，出于内存的高效利用考虑，还要进行内存对齐

```go
// runtime/slice.go
// func growslice(et *_type, old slice, cap int) slice {}
case et.size == sys.PtrSize: // 8
    lenmem = uintptr(old.len) * sys.PtrSize // 一个int占用8个字节，共2 * 8 = 16字节
    newlenmem = uintptr(cap) * sys.PtrSize // 预估容量5 * 8字节 = 40字节
    capmem = roundupsize(uintptr(newcap) * sys.PtrSize)　// 此次扩容需要申请的内存大小 6 * 8 = 48字节
    overflow = uintptr(newcap) > maxAlloc/sys.PtrSize // false
    newcap = int(capmem / sys.PtrSize) // newcap最终是6
```

下面是内存对齐的过程：

```go
// runtime/msize.go
// Returns size of the memory block that mallocgc will allocate if you ask for the size.
func roundupsize(size uintptr) uintptr {
	if size < _MaxSmallSize {
		if size <= smallSizeMax-8 {
            // divRoundUp(size, smallSizeDiv)　向上取整。47/8 = 6
			return uintptr(class_to_size[size_to_class8[divRoundUp(size, smallSizeDiv)]])
		} else {
			return uintptr(class_to_size[size_to_class128[divRoundUp(size-smallSizeMax, largeSizeDiv)]])
		}
	}
	if size+_PageSize < size {
		return size
	}
	return alignUp(size, _PageSize)
}

```

所需内存 = 预估容量 * 元素类型大小

内存这里需要了解`golang`的内存管理模块，源码在`runtime/sizeclasses.go`

```go
// class  bytes/obj  bytes/span  objects  tail waste  max waste
//     1          8        8192     1024           0     87.50%
//     2         16        8192      512           0     43.75%
//     3         24        8192      341           8     29.24%
//     4         32        8192      256           0     21.88%
//     5         48        8192      170          32     31.52%
//     6         64        8192      128           0     23.44%
//     7         80        8192      102          32     19.07%
//     8         96        8192       85          32     15.95%
//     9        112        8192       73          16     13.56%
...


// go采用的是基于tcmalloc进行的内存分配，也就是go语言自己实现的内存分配器。
// 内存划分规则
var class_to_size = [_NumSizeClasses]uint16{0, 8, 16, 24, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 256, 288, 320, 352, 384, 416, 448, 480, 512, 576, 640, 704, 768, 896, 1024, 1152, 1280, 1408, 1536, 1792, 2048, 2304, 2688, 3072, 3200, 3456, 4096, 4864, 5376, 6144, 6528, 6784, 6912, 8192, 9472, 9728, 10240, 10880, 12288, 13568, 14336, 16384, 18432, 19072, 20480, 21760, 24576, 27264, 28672, 32768}

```

申请内存时，选择相近的，且大于等于需要的大小

总结一下，扩容一共分三步：

- 计算预估容量大小 
- 计算扩容后需要占用的内存大小

- 计算最终容量大小
