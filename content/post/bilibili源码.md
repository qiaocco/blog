---
title: "Bilibili接口分析"
date: 2021-06-08T18:16:34+08:00
draft: true
---

### 接口分析：/search/default

打开B站的首页，可以看到其调用`/x/web-interface/search/default`接口获取推荐的搜索内容

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210608181854.png)

返回的数据格式为

```javascript
{
  "code": 0,
  "message": "0",
  "ttl": 1,
  "data": {
    "seid": "14451654524366534119",
    "id": 8554957115754187384,
    "show_name": "《你的名字》预告剪辑师来B站投稿啦！",
    "name": "av51996129",
    "type": 0
  }
}
```

而我们在`app/interface/main/web/http/http.go`中可以看到相关路由的注册的代码

```cpp
// line 47
group := e.Group("/x/web-interface", bm.CSRF(), bm.CORS())
// line 112
searchGroup := group.Group("/search")
{
    searchGroup.GET("/all", authSvr.Guest, searchAll)
    searchGroup.GET("/type", authSvr.Guest, searchByType)
    searchGroup.GET("/recommend", authSvr.Guest, searchRec)
    searchGroup.GET("/default", authSvr.Guest, searchDefault)
    searchGroup.GET("/egg", searchEgg)
}
```

也就是说`searchDefault`函数将会处理`/x/web-interface/search/default`的请求。

我们看下`searchDefault`的实现：

```go
// app/interface/main/web/http/search.go
func searchDefault(c *bm.Context) {
	var (
		mid   int64
		buvid string
		err   error
	)
	v := new(struct {
		FromSource string `form:"from_source"`
	})
	if err = c.Bind(v); err != nil {
		return
	}
	if ck, err := c.Request.Cookie("buvid3"); err == nil {
		buvid = ck.Value
	}
	if midInter, ok := c.Get("mid"); ok {
		mid = midInter.(int64)
	}
	c.JSON(webSvc.SearchDefault(c, mid, v.FromSource, buvid, c.Request.Header.Get("User-Agent")))
}
```

获取了一些参数后， 交给service目录下的SearchDefault处理

```go
// app/interface/main/web/service/search.go

// SearchDefault get search default word.
func (s *Service) SearchDefault(c context.Context, mid int64, fromSource, buvid, ua string) (data *model.SearchDefault, err error) {
	data, err = s.dao.SearchDefault(c, mid, fromSource, buvid, ua)
	return
}

```

然后由dao.SearchDefault处理

```go
// app/interface/main/web/dao/search.go
// SearchDefault get search default word.
func (d *Dao) SearchDefault(c context.Context, mid int64, fromSource, buvid, ua string) (data *model.SearchDefault, err error) {
	var (
		params = url.Values{}
		ip     = metadata.String(c, metadata.RemoteIP)
	)
	params.Set("main_ver", _searchVer)
	params.Set("platform", _searchPlatform)
	params.Set("clientip", ip)
	params.Set("userid", strconv.FormatInt(mid, 10))
	params.Set("search_type", "default")
	params.Set("from_source", fromSource)
	params.Set("buvid", buvid)
	var req *http.Request
	if req, err = d.httpSearch.NewRequest(http.MethodGet, d.searchDefaultURL, ip, params); err != nil {
		return
	}
	req.Header.Set("browser-info", ua)
	var res struct {
		Code   int    `json:"code"`
		SeID   string `json:"seid"`
		Tips   string `json:"recommend_tips"`
		Result []struct {
			ID       int64  `json:"id"`
			Name     string `json:"name"`
			ShowName string `json:"show_name"`
			Type     string `json:"type"`
		} `json:"result"`
	}
	if err = d.httpSearch.Do(c, req, &res); err != nil {
		log.Error("Search d.httpSearch.Get(%s) error(%v)", d.searchDefaultURL, err)
		return
	}
	if res.Code != ecode.OK.Code() {
		log.Error("Search d.httpSearch.Do(%s) code error(%d)", d.searchDefaultURL, res.Code)
		err = ecode.Int(res.Code)
	}
	if len(res.Result) == 0 {
		err = ecode.NothingFound
		return
	}
	data = &model.SearchDefault{}
	for _, v := range res.Result {
		data.Trackid = res.SeID
		data.ID = v.ID
		data.ShowName = v.ShowName
		data.Name = v.Name
	}
	return
}

```

