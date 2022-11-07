from requests import post

class DiscordWebhook:
    def __init__(self, hook) -> None:
        self.hook = hook
    
    def restock(self, site: str, pid: str, title: str, image: str, price: str, timestamp: str) -> int:
        data = { 
            "embeds": [
                {
                    "title": title,
                    "url": f"https://www.saturn.de/de/product/_just-restocked-{pid}.html",
                    "color": 8729748,
                    "fields": [
                        {
                            "name": "Site",
                            "value": site,
                            "inline": True
                        },
                        {
                            "name": "PID",
                            "value": pid,
                            "inline": True
                        },
                        {
                            "name": "Price",
                            "value": price,
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": timestamp
                    }, 
                    "thumbnail": {
                        "url": image
                    }
                }
            ]
        }
        return post(self.hook, json=data).status_code