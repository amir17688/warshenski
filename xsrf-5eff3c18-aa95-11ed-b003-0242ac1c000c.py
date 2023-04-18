'''
Author; Garrett Breeden
Version: 1.0
    1. Integrated SeleniumDriver into GUI 
        - Data should now pass from GUI -> Selenium
    2. Updated input field classes
    3. Small GUI Tweaks

Version: 1.2
    1. Corrected issue with data being passed to Selenium from GUI


TO ONLY BE USED BY L2 AND L3 @ PARTECH
'''
from Tkinter import *
from SeleniumDriver import *
import pyperclip
# import ttk               ONLY GOOD FOR STYLE


class JiraGeneratorWindow():
    username = None
    password = None

    summary = None
    clarify = None
    details = None

    def __init__(self, master, selenium):
        self.master = master
        master.title("Jira Automation")
        self.firefox = selenium
        #        #
        # CONFIG #
        #        #
        self.colorWhiteText = '#FFF'
        self.colorGreyBackground = '#708090'
        #           #
        # </CONFIG> #
        #           #
        empty_spacer_1 = Label(master, text=" ")
        empty_spacer_1.grid(column=0, row=0)

        self.login_button = Button(
            master, text="JIRA Login", command=self.setCredentials)
        self.login_button.grid(sticky="E", column=3, row=0)

        self.summary_static_text = Label(
            master, text="Input Sync Summary:")
        self.summary_static_text.grid(columnspan=4, sticky='W', row=1)

        self.summary_field = Entry(root, width=61,)
        self.summary_field.configure(
            background=self.colorGreyBackground, foreground=self.colorWhiteText)
        self.summary_field.grid(columnspan=4, column=0, row=2, sticky="W")

        empty_spacer_2 = Label(master, text=" ")
        empty_spacer_2.grid(column=0, row=3)

        self.clarify_static_text = Label(
            master, text="Input Case Number:")
        self.clarify_static_text.grid(columnspan=4, sticky='W', row=4)

        self.clarify_field = Entry(root, width=61)
        self.clarify_field.configure(
            background=self.colorGreyBackground, foreground=self.colorWhiteText)
        self.clarify_field.grid(column=0, row=5, columnspan=4, sticky="W")

        empty_spacer_3 = Label(master, text=" ")
        empty_spacer_3.grid(column=0, row=6)

        self.detailed_static_text = Label(
            master, text="Input Detailed Information")
        self.detailed_static_text.grid(columnspan=4, sticky="W", row=7)

        self.detailed_field = Text(root, height=35, width=79)
        self.detailed_field.configure(
            background=self.colorGreyBackground, foreground=self.colorWhiteText)
        self.detailed_field.grid(columnspan=4, row=8, column=0, sticky="W")

        self.run_split_button = Button(
            master, text="Create JIRA", command=self.createCase)
        self.run_split_button.grid(row=10, column=1, sticky="W")

        self.close_button = Button(master, text="Close", command=master.quit)
        self.close_button.grid(row=10, column=2, sticky="E")

    # Create TopLevel Pane to Input Credentials
    def setCredentials(self):
        self.win = Toplevel()
        self.win.title = "Input JIRA Login"

        self.username_static_text = Label(self.win, text="Username:")
        self.username_static_text.grid(column=0, row=0, sticky="E")

        self.username_field = Entry(self.win)
        self.username_field.configure(
            background=self.colorGreyBackground, foreground=self.colorWhiteText)
        self.username_field.grid(column=1, row=0, sticky="W")

        self.password_static_text = Label(self.win, text="Password:")
        self.password_static_text.grid(column=0, row=1, sticky="E")

        self.password_field = Entry(self.win, show="*")
        self.password_field.configure(
            background=self.colorGreyBackground, foreground=self.colorWhiteText)
        self.password_field.grid(column=1, row=1, sticky="W")

        self.submit_button = Button(self.win, text="Save Credentials", command=self.setLoginInfo)
        self.submit_button.grid(column=1, row=2, columnspan=2)

    # Set the login information to the class member
    def setLoginInfo(self):
        self.password = self.password_field.get()
        self.username = self.username_field.get()
        self.destroy_window(self.win)

    # Error popup notification function
    def errorNotification(self, error_message):
        self.error_window = Toplevel()
        self.error_window.title = "ERROR - PLEASE READ"
        error_message_text = Message(
            self.error_window, text=error_message, width=500)
        error_message_text.grid(row=0, column=0, columnspan=3)

        close_button_error = Button(
            self.error_window, text="Ok", command=lambda: self.error_window.destroy())
        close_button_error.grid(row=1, column=1)

    # closes passed window
    def destroy_window(self, window):
        window.destroy()

    def createCase(self):
        # Ensures JIRA button has been at least clicked before allowing script to execute.
        if(self.password == None or self.username == None or self.password == ' ' or self.username == ' '):
            self.errorNotification(
                "Please login to JIRA first")
        else:
            self.firefox.loadPage("https://devops.partech.com/jira/login.jsp", "JIRA")
            self.firefox.login(self.username, self.password)
            self.firefox.createNewTicket()
            self.firefox.inputDataToCase(self.summary_field.get(), self.detailed_field.get("1.0", END))
            #TODO: Link GUI Input to Selenium.    


if(__name__ == "__main__"):
    root = Tk()
    _selenium = SeleniumDriver()
    main_GUI = JiraGeneratorWindow(root, _selenium)
    root.mainloop()

    # <div class="aui-message aui-message-success"
    # <a class="issue-created-key issue-link" data-issue

