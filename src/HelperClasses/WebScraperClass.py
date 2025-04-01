import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class WebScraperClass:

    def __init__(self):
        # Instance attributes
        self.url = "https://namazvakitleri.diyanet.gov.tr/de-DE/11002/gebetszeit-fur-berlin"
        

    def get_prayer_times(self):
        current_date_raw = datetime.now()
        tomorrow_date_raw = current_date_raw + timedelta(days=1)
        current_date = current_date_raw.strftime("%d.%m.%Y")
        tomorrow_date = tomorrow_date_raw.strftime("%d.%m.%Y")
        prayer_time_dic = {"requestSuccess": [False, current_date] ,"Prayers":[], "nextDayPrayers": {"date": tomorrow_date, "prayers":[]}}
        
        try:
            response = requests.get(self.url, timeout=120) 
            if (response.status_code == 200):
                soup = BeautifulSoup(response.text, 'html.parser')
                prayer_time_dic["requestSuccess"][0] = True
                desired_date_row = soup.find('td', text=current_date).parent
                current_prayer_times = [td.text.strip() for td in desired_date_row.find_all('td')[2:]]
                prayer_time_dic["Prayers"] = current_prayer_times
                
                desired_date_row = soup.find('td', text=tomorrow_date).parent
                tomorrows_prayer_times = [td.text.strip() for td in desired_date_row.find_all('td')[2:]]
                prayer_time_dic["nextDayPrayers"]["prayers"] = tomorrows_prayer_times
                
            else:
                print("Couldnt get the data.")
                prayer_time_dic["requestSuccess"][0] = False
            return prayer_time_dic
        except Exception as e:
            print(e)
            prayer_time_dic["requestSuccess"][0] = False
            return prayer_time_dic
        except requests.Timeout:
            prayer_time_dic["requestSuccess"][0] = False
            return prayer_time_dic
        
scraper = WebScraperClass()
scraper.get_prayer_times()
            