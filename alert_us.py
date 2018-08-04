"""
Send an email when some crazy shit goes on
"""


import yagmail

class email_us:

    yag = yagmail.SMTP("lss6@rice.edu")
    to_addr = None
    msg = None

    def send_email(self, to_address_list: list, subject: str, message: str):
        """
        Send an email. 
        """
        self.yag.send(to=to_address_list, subject=subject, contents=message)





