# Author: Styfen Schaer <schaers@student.ethz.ch> 

import bs4
import requests
import time
from datetime import datetime
from twilio.rest import Client


class Webpage:
    """ Creates a webpage object which can be handled and monitored by the notifier """
    def __init__(self, url):
        self.url = url
        self.webtext = self.get_webtext()


    def get_webtext(self):
        """ Returns the current webtext from corresponding URL.
        If webpage is not accessible the old webtext is returned instead """
        try:
            response = requests.get(self.url)
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            for script in soup(['script', 'style']):
                script.extract()
            return soup.get_text()
        except Exception:
            return self.webtext


    def has_changed(self):
        """ Checks if webtext has changed """
        webtext = self.get_webtext()
        changed = (webtext != self.webtext)
        self.webtext = webtext
        return changed


class Notifier:
    """ Creates a notifier which either notifies via terminal or whatsapp. 
    If you want to use whatsapp notification you need twilio: https://www.twilio.com/
    Regarding twilio, this video might be helpful: https://www.youtube.com/watch?v=98OewpG8-yw&ab_channel=Twilio
    See README for more. """
    def __init__(self, settings, client_info=None):
        self.period = settings['monitoring period']
        self.t_status_report = settings['interval for status report']
        self.t_sleep = settings['time asleep']

        self.notification_method = settings['notification method']
        if self.notification_method == 'whatsapp':
            self.client = Client(client_info['account sid'], client_info['auth token'])
            self.from_whatsapp_number = client_info['sender']
            self.to_whatsapp_number = client_info['recipient']

        self.pages = []
        self.init_time = time.time()
        self.last_report = time.time()


    def add_pages(self, *args):
        """ Add additional page(s) you want to be monitored """
        for url in args:
            self.pages.append(Webpage(url))


    def look_up(self):
        """ Returns all webpages which webtext has changed """
        changed_pages = []
        for page in self.pages:
            if page.has_changed():
                changed_pages.append(page)
        return changed_pages


    @staticmethod
    def gen_message(pages, title):
        """ Generates and returns a message.
        Change this function as you like. """
        datetime_ = datetime.fromtimestamp(time.time())
        message = '--- {0} --- \n{1}'.format(title, datetime_)
        for page in pages:
            message = message + '\n{0} has changed'.format(page.url)
        return message

    
    def report(self):
        """ Creates and submits a report in the given interval """
        if time.time() - self.last_report > self.t_status_report:
            changed_pages = self.look_up()
            message = Notifier.gen_message(changed_pages, title='Status report')
            self.send(message)
            self.last_report = time.time()


    def news(self):
        """ Creates and submits a message if a webtext has changed """
        changed_pages = self.look_up()
        if len(changed_pages) > 0:
            message = Notifier.gen_message(changed_pages, title='News')
            self.send(message)


    def send(self, message):
        """ Sends or prints the passed message """
        if self.notification_method == 'whatsapp':
            self.client.messages.create(body=message,
                                        from_=self.from_whatsapp_number,
                                        to=self.to_whatsapp_number)
        elif self.notification_method == 'terminal':
            print(message)

    
    def run(self):
        """ Run notifier for given monitoring period """
        while time.time() - self.init_time < self.period:
            self.news()
            self.report()
            time.sleep(self.t_sleep)


if __name__ == '__main__':
    """ All times in seconds. Notification method is either 'terminal' or 'whatsapp' 
    - monitoring period: how long you want to run the notifier
    - time asleep: time interval to check the webpages for changes
    - interval for status report: send a notification in given interval
    - notification method: either 'terminal' or 'whatsapp' """
    settings = {'monitoring period': 24*3600,  
                'time asleep': 10,
                'interval for status report': 2*3600,
                'notification method': 'terminal'} 
    
    """ If you want to send a whatsapp message via twilio (see README for more) fill in these information 
    - account sid: your account sid
    - auth token: your auth token
    - sender: phone number of the sender (twilio)
    - recipient: reciepient's number (yours) """    
    client_info = {'account sid': '##################################',  
                   'auth token': '################################',  
                   'sender': 'whatsapp:+###########',  
                   'recipient': 'whatsapp:+###########'}  
                
    """ Inititialize the Notifier. 
    Omit the client_info if you don't have them or if you don't want to notify via whatsapp. """ 
    myPageHunter = Notifier(settings=settings, client_info=client_info)
    
    """ Add pages you want to monitor """   
    pages_to_monitor = ['https://github.com/', 'https://en.wikipedia.org/wiki/Main_Page']
    myPageHunter.add_pages(*pages_to_monitor)
    
    """ Run the notifier """    
    myPageHunter.run()

