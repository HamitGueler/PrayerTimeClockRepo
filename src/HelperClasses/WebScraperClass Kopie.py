import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class WebScraperClass:

    def __init__(self):
        # Instance attributes
        self.url = "https://namazvakitleri.diyanet.gov.tr/de-DE/11002/gebetszeit-fur-berlin"
        self.url2 = "https://www.edarabia.com/prayer-times-berlin/#:~:text=Today's%20Prayer%20Time%20Berlin%20are,Prayer%20Time%2006%3A26%20PM."
        

    def get_prayer_times(self):
        try:
            response = requests.get(self.url)
            response2 = requests.get(self.url2)
            print("!")
            print(response2)
            current_date_raw = datetime.now()
            tomorrow_date_raw = current_date_raw + timedelta(days=1)
            current_date = current_date_raw.strftime("%d.%m.%Y")
            tomorrow_date = tomorrow_date_raw.strftime("%d.%m.%Y")

            
            prayer_time_dic = {"requestSuccess": [False, current_date] ,"Prayers":[], "nextDayPrayers": {"date": tomorrow_date, "prayers":[]}}

            soup2 = BeautifulSoup(response2.text, 'html.parser')
            times_list = soup2.find('h6', string='Muslim World League (MWL) (Hanafi)')
            h6_tag = soup2.find('h6', string='Muslim World League (MWL) (Hanafi)')

            # Wenn das <h6>-Tag gefunden wurde, den übergeordneten <div> extrahieren
            if h6_tag:
                parent_div = h6_tag.find_parent('div')
                times = parent_div.find_all('li')
                for time in times:
                    if ' - ' in time.get_text():
                        prayer, time_str = time.get_text().split(' - ')
                        print(f"{prayer}: {time_str}")
                    else:
                        print(f"Unrecognized entry: {time.get_text()}")
            else:
                print("Der <h6>-Tag mit dem Text wurde nicht gefunden.")
                
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
        
scraper = WebScraperClass()
scraper.get_prayer_times()
            