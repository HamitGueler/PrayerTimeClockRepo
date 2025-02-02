import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser
class WebScraperClass:

    def __init__(self):
        self.url = "https://www.edarabia.com/prayer-times-berlin/#:~:text=Today's%20Prayer%20Time%20Berlin%20are,Prayer%20Time%2006%3A26%20PM."
        

    def get_prayer_times(self):
        current_date_raw = datetime.now()
        tomorrow_date_raw = current_date_raw + timedelta(days=1)
        current_date = current_date_raw.strftime("%d.%m.%Y")
        tomorrow_date = tomorrow_date_raw.strftime("%b %d")
        prayer_time_dic = {"requestSuccess": [False, current_date] ,"Prayers":["00:00"] * 5, "nextDayPrayers": {"date": tomorrow_date_raw.strftime("%d.%m.%Y"), "prayers":["00:00"] * 5}}
        try:
            response = requests.get(self.url, timeout=120) 
            if (response.status_code == 200):
                soup = BeautifulSoup(response.text, 'html.parser')                
                prayer_time_dic["requestSuccess"][0] = True
                
                h6_tag = soup.find('h6', string='Muslim World League (MWL) (Hanafi)')
                time_list = []

                if h6_tag:
                    parent_div = h6_tag.find_parent('div')
                    times = parent_div.find_all('li')
                    for time in times:
                        if ' - ' in time.get_text():
                            prayer, time_str = time.get_text().split(' - ')
                            time_list.append(time_str)

                        else:
                            print(f"Unrecognized entry: {time.get_text()}")
                            prayer_time_dic["requestSuccess"][0] = False
                            return prayer_time_dic

                    prayer_time_dic["Prayers"] = [parser.parse(time).strftime('%H:%M') for time in time_list]
                else:
                    print("Der <h6>-Tag mit dem Text wurde nicht gefunden.") 
                    prayer_time_dic["requestSuccess"][0] = False
                    return prayer_time_dic
                
                desired_date_row = soup.find('td', text=tomorrow_date).parent
                tomorrows_prayer_times = [td.text.strip() for td in desired_date_row.find_all('td')[1:]]
                prayer_time_dic["nextDayPrayers"]["prayers"] = [parser.parse(time).strftime('%H:%M') for time in tomorrows_prayer_times]
                
            else:
                print("Couldnt get the data.")
                prayer_time_dic["requestSuccess"][0] = False
                return prayer_time_dic
            return prayer_time_dic
        except requests.Timeout:
            prayer_time_dic["requestSuccess"][0] = False
            return prayer_time_dic
        except Exception as e:
            print(e)
            prayer_time_dic["requestSuccess"][0] = False
            return prayer_time_dic
        
#scraper = WebScraperClass()
#scraper.get_prayer_times()
            