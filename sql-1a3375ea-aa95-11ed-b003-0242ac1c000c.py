# CLI query interface for Ebola database in Python
import pymysql
from db_connect import *
from query_functions import *

def print_menu():
    print ('\nQuery options:')
    print ('1:  List ETCs in the country __ having more than __ open beds.')
    print ('2:  List average age & education of respondents whose sex=__ and live in __.')
    print ('3:  Count the respondents whose sex=__ and who have at least an education of __.')
    print ('4:  Display partner organizations with their longitude/latitude coordinates.')
    print ('5:  Display a chosen organization __ & codes of the ETCs it is working with.')
    print ('6:  Display all distinct organization types.')
    print ('7:  Display every respondent\'s (whose sex=__) info & their country\'s info.')
    print ('8:  Display every ETC that isn\'t closed & its info/partner organization.')
    print ('9:  List countries in ascending order by GDP.')
    print ('10: Count the respondents (with sex=__, education>=__, and country=__) who think their community was well organized.')
    print ('11: Show gender, age, education, and country of survey respondents ordered by age.')
    print ('12: Show ETC names and Partner Orgs ordered by ETC names.')
    print ('13: Show ETC name, Selected Partner Org, and Country GDP ordered by Country.')
    print ('14: Show average age of selected gender of survey respondents.')
    print ('15: Show average educaiton level of selected gender of survey respondents.\n')

def run_another():
    opt = raw_input('Run another query? (y/n): ')
    if (opt == 'y' or opt == 'Y'):
        print_menu()
        run_query_case()
    else:
        print('Goodbye.')

def run_query_case():
    case = int(input('Enter query option number: '))
    if (case == 1):
        etc_open_beds()
        run_another()
    elif (case == 2):
        age_edu_sex_country()
        run_another()
    elif (case == 3):
        count_sex_educ()
        run_another()
    elif (case == 4):
        partner_lat_long()
        run_another()
    elif (case == 5):
        org_ETC_codes()
        run_another()
    elif (case == 6):
        distinct_org_types()
        run_another()
    elif (case == 7):
        respondent_country_info()
        run_another()
    elif (case == 8):
        non_closed_ETC_partner()
        run_another()
    elif (case == 9):
        country_gdp()
        run_another()
    elif (case == 10):
        count_organized()
        run_another()
    elif (case == 11):
        surveyresp_country_byAge()
        run_another()
    elif (case == 12):
        etc_limited_byName()
        run_another()
    elif (case == 13):
        partner_org_limited_byCountry()
        run_another()
    elif (case == 14):
        avg_age_resp()
        run_another()
    elif (case == 15):
        avg_edu_resp()
        run_another()
    else:
        print("Sorry, that is not an option.")
        run_another()


# run_insert error checking
# ...


def main():
    print ('========= QUERY INTERFACE FOR EBOLA DATABSE =========\n')

    # create views
    print ('...Creating views')
    create_view_SurveyResp_Country()
    create_view_etc_limited()
    
    # print query options menu
    print_menu()
    
    # prompt user for query option
    run_query_case()

    print('\n============== END PROGRAM ==============')
main()
