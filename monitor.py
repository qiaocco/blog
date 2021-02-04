import requests


def send_to_wx(text, desp=None):
    """使用server酱向微信发消息
    text: 消息标题
    desp: 消息详情
    """
    url = (
        "https://sc.ftqq.com/SCU9800T1aa9ee59f94cfe6bcde0b23b4b91135d5959fab2590de.send"
    )
    params = {"text": text, "desp": desp}
    requests.get(url, params=params)


def fetch(url):
    try:
        requests.get(url)
    except Exception as e:
        send_to_wx("网站异常啦", f"url={url}, {e}")
    else:
        send_to_wx("网站正常")


if __name__ == "__main__":
    fetch("https://blog.qiaocci.com")