from json import loads, dumps
from uuid import uuid4
from time import sleep
from threading import Thread 
from utility import create_logger, get_bypass_headers, get_proxy
from database import DatabaseManager
from discord import DiscordWebhook 
from datetime import datetime 
from cloudscraper import CloudScraper, create_scraper 
from sys import argv, exit
try:
    import helheim
except:
    print("Helheim not installed")

def injection(session, response): 
    if helheim.isChallenge(session, response): return helheim.solve(session, response)
    else: return response

def get_session(hel: bool): 
    if not hel:
        session = create_scraper(
            browser={
                "custom": "flutterapp - ios - 4.34.1+2021000521"
            }
        )  
    else:
        session = create_scraper(
            browser={
                "custom": "flutterapp - ios - 4.34.1+2021000521"
            },
            requestPostHook=injection,
            captcha={
                'provider': '2captcha', 
                'api_key': twocaptcha
            }
        ) 
        helheim.wokou(session)
    return session

class RestockMonitor:
    def __init__(self, links: list, site_settings: dict, monitor_settings: dict) -> None:
        """Initialize and start the RestockMonitor instance (direcly pids monitor)

        Args:
            links (list): Links/pids to monitor
            site_settings (dict): Static settings for MMS/Saturn
            monitor_settings (dict): Settings for the monitor instance
        """        
        self.pids = [l.split('/')[-1].split('-')[-1].split('.')[0] for l in links]
        self.mode = "RESTOCK"
        self.domain, self.header = list(site_settings.values())
        self.error_delay, self.normal_delay, self.helehim_active, self.proxyless = list(monitor_settings.values())
        for pid in self.pids: Thread(target=self.start, args=[pid]).start()
    
    def inizialize_session(self, session: CloudScraper) -> bool:
        """In order to solve/prevent cf challenge

        Args:
            session (CloudScraper): Cloudscraper session to use

        Returns:
            bool: Cf hit?
        """        
        try: session.get(f"https://www.{self.domain}.de/")
        except: return False
        else: return True 

    def start(self, pid: str) -> None: 
        """Start the monitor instance for specific pid

        Args:
            pid (str): Pid to monitor
        """        
        database = DatabaseManager(self.header)
        api_call = "GetSelectProduct"
        query = {
            "operationName": api_call,
            "variables": dumps({"hasMarketplace":True,"isDemonstrationModelAvailabilityActive":False,"withMarketingInfos":False,"isFinancingDisplayActive":True,"id":pid}),
            "extensions": dumps({"persistedQuery":{"version":1,"sha256Hash":"a0bf36f44fd779e2fe34cd5c7446a7fa411105735a60edb72b9287bb3add7819"},"pwa":{"salesLine":self.header,"country":"DE","language":"de","globalLoyaltyEnrollment":True,"globalLoyaltyProgram":True,"fifaUserCreation":True}})
        }
        logger.info(f"{self.mode} | {pid} | Starting...")
        item = [i for i in database.connection.execute(f'SELECT * FROM restocks WHERE pid = "{pid}"')][0]
        
        # Inizialize session 
        cf_hit = False
        cf_blocks = 0
        checks_done = 0 # Will let u know how many times it successfully loaded the endpoint data
        api_url = f"https://www.{self.domain}.de/api/v1/graphql" 
        
        while 1: 

            # If got 2 cf hits in a row the same proxy, rotate it
            if cf_blocks == 2:
                logger.info(f"{self.mode} | {pid} | {checks_done} | Too much CF blocks, changing session")
                cf_hit, cf_blocks = False, 0
            # If got a cf hit, so challenge has been solved, don't rotate proxy
            if not cf_hit:
                logger.info(f"{self.mode} | {pid} | {checks_done} | Rotating proxies...")
                cf_blocks = 0
                session = get_session(self.helehim_active)  
                if not self.proxyless:
                    proxy = get_proxy()
                    if proxy: session.proxies.update(proxy) 
            try:
                res = session.get(api_url, params=query, headers=get_bypass_headers(self, api_call))  
            except Exception as e:
                logger.error(f"{self.mode} | {kws} | {checks_done} | Unexcepted error sending request: {str(e)}")
                session = get_session(self.helehim_active)  
                if not self.proxyless:
                    proxy = get_proxy()
                    if proxy: session.proxies.update(proxy) 
                sleep(self.error_delay)
                continue
            else:
                if res.status_code in [403, 429]:
                    logger.error(f"{self.mode} | {pid} | {checks_done} | CF Hit, solving...")
                    cf_hit = self.inizialize_session(session)
                    cf_blocks += 1
                    logger.info(f"{self.mode} | {pid} | {checks_done} | CF Solved -> {cf_hit}")
                    sleep(self.error_delay)
                    continue 
                try:
                    data = res.json()['data']
                except Exception as e:
                    # logger.exception(e)
                    logger.error(f"{self.mode} | {pid} | {checks_done} | Unexcepted error loading request response: {res.status_code} / {str(e)}")
                    sleep(self.error_delay)
                    continue
                else:
                    try:
                        product_data = data['productAggregate']
                        status = product_data["availability"]['delivery']['availabilityType'] 
                        if status not in [item[5], "NONE"]:
                            title = product_data['product']['title']
                            try: image = product_data['product']['assets'][0]['link'] 
                            except: 
                                # Default image when error loading the product one
                                image = "https://cdn.freebiesupply.com/logos/large/2x/saturn-1-logo-png-transparent.png"
                            try: price = f"{product_data['price']['price']} {product_data['price']['currency']}"
                            except: price = "?"
                            logger.info(f"{self.mode} | {pid} | {checks_done} | Restock caught")
                            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                            cur = database.connection.cursor()   
                            cur.execute(f"UPDATE restocks SET title='{title}', image='{image}', price='{price}', status='{status}', last_change='{timestamp}' WHERE pid = '{pid}'")
                            database.connection.commit()   
                            item = (0, pid, title, image, price, status, 0, 0)
                            webhook.restock(self.header, pid, title, image, price, timestamp)
                        else: 
                            if status != item[5]: 
                                item = (0, pid, 0, 0, 0, status, 0, 0)
                                cur = database.connection.cursor()   
                                cur.execute(f"UPDATE restocks SET status='{item[5]}' WHERE pid = '{pid}'")
                                database.connection.commit() 
                            logger.info(f"{self.mode} | {pid} | {checks_done} | Nothing new")
                        checks_done += 1
                        sleep(self.normal_delay) 
                    except Exception as e:
                        logger.error(f"{self.mode} | {pid} | {checks_done} | Unexcepted error parsing request response: {res.status_code} / {str(e)}")
                        sleep(self.error_delay)
                    else: sleep(self.normal_delay)
                    finally: continue


class KeywordsMonitor:
    def __init__(self, kws_list: list, site_settings: dict, monitor_settings: dict) -> None: 
        """Initialize and start the KeywordsMonitor instance (kws monitor)

        Args:
            links (list): Links/pids to monitor
            site_settings (dict): Static settings for MMS/Saturn
            monitor_settings (dict): Settings for the monitor instance
        """       
        self.mode = "KEYWORDS"
        self.domain, self.header = list(site_settings.values())
        self.error_delay, self.normal_delay, self.helehim_active, self.proxyless = list(monitor_settings.values())
        for kws in kws_list: Thread(target=self.start, args=[kws]).start()
    
    def inizialize_session(self, session) -> bool: 
        """In order to solve/prevent cf challenge

        Args:
            session (CloudScraper): Cloudscraper session to use

        Returns:
            bool: Cf hit?
        """        
        try: session.get(f"https://www.{self.domain}.de/")
        except: return False
        else: return True
    
    def start(self, kws: str) -> None: 
        """Start the monitor instance for specific kws

        Args:
            kws (str): Kws to monitor
        """      
        database = DatabaseManager(self.header)
        api_call = "SearchV4"
        logger.info(f"{self.mode} | {kws} | Starting...")
        kws_data = loads([i for i in database.connection.execute(f'SELECT * FROM kws_db WHERE kws = "{kws}"')][0][2]) 

        # Inizialize session 
        cf_hit = False
        cf_blocks = 0
        checks_done = 0 # Will let u know how many times it successfully loaded the endpoint data
        api_url = f"https://www.{self.domain}.de/api/v1/graphql" 

        while 1:

            # If got 2 cf hits in a row the same proxy, rotate it
            if cf_blocks == 2:
                logger.info(f"{self.mode} | {kws} | {checks_done} | Too much CF blocks, changing session")
                cf_hit, cf_blocks = False, 0
            # If got a cf hit, so challenge has been solved, don't rotate proxy
            if not cf_hit:
                logger.info(f"{self.mode} | {kws} | {checks_done} | Rotating proxies...")
                cf_blocks = 0
                session = get_session(self.helehim_active)  
                if not self.proxyless:
                    proxy = get_proxy()
                    if proxy: session.proxies.update(proxy)  
                _id = str(uuid4()) 
                session.cookies.set("ts_id", _id)
                querystring = {
                    "operationName":api_call,
                    "variables": dumps({"hasMarketplace":True,"isRequestSponsoredSearch":True,"maxNumberOfAds":0,"isDemonstrationModelAvailabilityActive":False,"withMarketingInfos":False,"experiment":"mp","filters":[],"page":1,"query":kws,"sessionId":_id,"customerId":_id,"pageSize":12,"pageType":"Search","productFilters":[]}),
                    "extensions":dumps({"persistedQuery":{"version":1,"sha256Hash":"cea399f70b7419f3c711261b4f53187b114999001b865578c5feb581c5dbdb40"},"pwa":{"salesLine":self.header,"country":"DE","language":"de","globalLoyaltyEnrollment":True,"globalLoyaltyProgram":True,"fifaUserCreation":True}})
                } 
            
            try:
                res = session.get(api_url, params=querystring, headers=get_bypass_headers(self, api_call)) 
            except Exception as e:
                # logger.exception(e)
                logger.error(f"{self.mode} | {kws} | {checks_done} | Unexcepted error sending request: {str(e)}")
                session = get_session(self.helehim_active)  
                if not self.proxyless:
                    proxy = get_proxy()
                    if proxy: session.proxies.update(proxy) 
                sleep(self.error_delay)
                continue
            else:
                if res.status_code in [403, 429]:
                    logger.error(f"{self.mode} | {kws} | {checks_done} | CF Hit, solving...")
                    cf_hit = self.inizialize_session(session)
                    cf_blocks += 1
                    logger.info(f"{self.mode} | {kws} | {checks_done} | CF Solved -> {cf_hit}")
                    sleep(self.error_delay)
                    continue 
                try:
                    products = res.json()['data']['searchV4']['products']
                except Exception as e:
                    # logger.exception(e)
                    logger.error(f"{self.mode} | {kws} | {checks_done} | Unexcepted error loading request response: {res.status_code} / {str(e)}")
                    sleep(self.error_delay)
                    continue
                else:
                    try:
                        new = False
                        for data in products:  
                            product_data = data['productAggregate']
                            pid = product_data['productId']  
                            try: status = product_data["availability"]['delivery']['availabilityType']
                            except: status = "NONE"
                            if not kws_data.get(pid) or status not in [kws_data.get(pid), "NONE"]:
                                title = product_data['product']['title']
                                try: image = f"https://assets.mmsrg.com/isr/166325/c1/-/{product_data['product']['titleImageId']}/mobile_200_200_png"
                                except: 
                                    # Default image when error loading the product one
                                    image = "https://cdn.freebiesupply.com/logos/large/2x/saturn-1-logo-png-transparent.png"
                                try: price = f"{product_data['price']['price']} {product_data['price']['currency']}"
                                except: price = "?"
                                logger.info(f"{self.mode} | {kws} | {checks_done} | New product found")
                                timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                                webhook.restock(self.header, pid, title, image, price, timestamp)
                                new = True 
                            kws_data[pid] = status
                        checks_done += 1
                        if not new: logger.info(f"{self.mode} | {kws} | {checks_done} | Nothing new")
                        else: 
                            logger.info(f"{self.mode} | {kws} | {checks_done} | Updated")
                            cur = database.connection.cursor()   
                            cur.execute(f"UPDATE kws_db SET data = '{dumps(kws_data)}', last_change='{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}' WHERE kws = '{kws}'")
                            database.connection.commit()   
                        sleep(self.normal_delay)
                    except Exception as e:
                        logger.error(f"{self.mode} | {kws} | {checks_done} | Unexcepted error parsing request response: {res.status_code} / {str(e)}")
                        sleep(self.error_delay)
                    else: sleep(self.normal_delay)
                    finally: continue

if __name__ == '__main__':  
    try:
        site = argv[1].lower()
        proxyless = "--proxyless" in argv
        helheim_active = "--no-helheim" not in argv
        kws_monitor_active = "--no-kws" not in argv
    except: 
        print("Invalid arguments provieded. Example 'py main.py mms")
        exit(0)
    
    if site == "saturn": site_settings = {"domain": "saturn","header": "Saturn"} 
    else: site_settings = {"domain": "mediamarkt","header": "Media"}   
    try: settings = loads(open("settings.json", "r").read())
    except:
        print("Invalid settings.json file.")
        exit(0)
    
    monitor_settings = {
        "error": settings['delay']['error'] / 1000,
        "normal": settings['delay']['normal'] / 1000,
        "helheim": helheim_active,
        "proxyless": proxyless
    }
    twocaptcha = settings['helheim']['2captcha']
    if helheim_active: helheim.auth(settings['helheim']['key'])  
    logger = create_logger(site_settings['domain'].upper())  
    database = DatabaseManager(site_settings['header'])
    webhook = DiscordWebhook(settings['hook'][site_settings['header']])
    
    print(f"Starting {site_settings['header']}'s RestockMonitor{' and KeywordsMonitor' if kws_monitor_active else ''} (Settings: proxyless={proxyless}, helheim={helheim_active})")
    
    pids = [str(i[1]) for i in database.connection.execute('SELECT * FROM restocks WHERE 1')]
    RestockMonitor(pids, site_settings, monitor_settings)
    
    if kws_monitor_active:
        kws = [i[1] for i in database.connection.execute('SELECT * FROM kws_db WHERE 1')]
        KeywordsMonitor(kws, site_settings, monitor_settings)