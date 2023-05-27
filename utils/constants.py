import os

token = os.getenv("PB_TG_TOKEN")
hosting_url = os.getenv("PB_URL")
table_name = os.getenv("PB_DB_TABLE_NAME")

default_day = None
default_time = "21:00"
default_target = 10
default_message = "5 goal di scarto e le squadre si _potrebbero_ cambiare \n" \
               "6 goal di scarto e le squadre si *devono* cambiare \n"\
               "(ditelo a chiunque invitate) \n"\
               "*PORTARE UNA MAGLIA BIANCA E UNA COLORATA*\n"
maybe_placeholder = "%is%maybe%present"