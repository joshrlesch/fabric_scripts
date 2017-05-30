import requests
import json
import re

from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from base_fabric import BaseFabric

Fabric = BaseFabric()

incoming_webhook_url = "https://hooks.slack.com/services/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"
modi_url = "https://fabric.io/hudl5/ios/apps/com.hudl.modie/issues?time=last-hour&event_type=all&subFilter=state&state=open&showAllBuilds=true"

groups = {
    "ANLYS": "core-analysis",
    "BBVB": "comp-bbvb-status",
    "CMSG": "core-messaging",
    # "COMM": Placeholder - no dedicated squad/channel
    "CP": "core-playlists",
    "FB": "comp-sideline",
    "GTM": "growth-team-mgmt",
    # HIT: Placeholder - no dedicated squad/channel
    "HULK": "comm-hulk",
    "i18n": "internationalization",
    "INT": "elite-integration",
    "LIB": "core-library-mobile",
    "LOKI": "comm-loki",
    "MFB": "comp-sideline",
    "MPS": "found-mobile",
    "MV": "core-mobile-video-exp",
    "RC": "found-mobile",
    "RS": "rs-mobile",
    "STAR": "comm-starfleet",
    "SWN": "comp-sideline",
    "TARS": "comm-tars-alerts",
    "VP": "core-video-perf",
    "BBALL": "comp-bbvb-status",  # Deprecated
    "COMP": "comp-bbvb-status",  # Deprecated
    "CTM": "growth-team-mgmt",  # Deprecated
    "MODI": "found-mobile",  # Deprecated
    "SOC": "comp-v3experience",  # Deprecated
    "SI": "elite-integration",  # Deprecated
    "SLD": "comm-qa",  # Deprecated
    "TM": "growth-team-mgmt",  # Deprecated
    "VI": "core-video-perf",  #Deprecated
    # "VP": "core-video-perf",  # Deprecated, VP still used
}

def get_table_of_crashes():
    try:
        Fabric.wait_until_visible_by('css selector', '.i_issue.open')
        try:
            return Fabric.driver.find_elements_by_css_selector('.i_issue.open')
        except StaleElementReferenceException as e:
            print("[get_table_of_crashes] Stale Element: {}".format(e))
            Fabric.driver.quit()
            exit()
    except TimeoutException:
        print("[get_table_of_crashes] No crashes in the last hour.")
        Fabric.driver.quit()
        exit()


def get_crash_info(crash):
    try:
        return crash.__getattribute__('text').splitlines()
    except StaleElementReferenceException as e:
        print("[crash_info] Stale element: {}".format(e))


def get_first_last_seen(crash_info):
    if '.' in crash_info[2] or '#' in crash_info[2] or '(' in crash_info[2]:
        if len(crash_info[2].split(' – ')) > 1:
            first_seen = crash_info[2].split(' – ')[0]
            last_seen = crash_info[2].split(' – ')[1]
        else:
            first_seen = crash_info[2]
            last_seen = crash_info[2]
    else:
        if len(crash_info[3].split(' – ')) > 1:
            first_seen = crash_info[3].split(' – ')[0]
            last_seen = crash_info[3].split(' – ')[1]
        else:
            first_seen = crash_info[3]
            last_seen = crash_info[3]
    first_seen = first_seen.split(" ")[1].replace("(","").replace(")", "")
    last_seen = last_seen.split(" ")[1].replace("(", "").replace(")", "")
    return first_seen, last_seen


def get_user(crash_index):
    Fabric.wait_until_clickable_by('xpath', '//*[@class="bg-white"]/tr[{}]'.format(crash_index)).click()
    Fabric.wait_until_clickable_by('css selector', '.button.green.inverse.ellipsis').click()
    Fabric.wait_until_visible_by('class name', 'cursor-pointer')
    email = Fabric.driver.find_element_by_class_name('cursor-pointer').get_attribute('text')
    name = get_name(email)
    return name


def get_name(email):
    unedited_name = re.search(r"([^@]+)(?=@)", email).group(0)
    name = unedited_name.replace(".", " ").title()
    return(name)


def extract_squad(name):
    try:
        squad = re.search(r"([A-Z]+)(?=-)", name).group(0)
        return squad
    except AttributeError:
        return "no-slack-room"


def message_content(crash_name, user_name, first_build, last_build, channels):
    return "\n"\
        "*Crash in Hudl Test: {}*\n"\
        "First seen in build _{}_ from #{}\n"\
        "Last seen in build _{}_ from #{}\n"\
        "last caused by user {}".format(crash_name, first_build, channels[0], last_build, channels[1], user_name)


def get_channels(first_squad, last_squad):
    try:
        first_channel = groups.get(first_squad)
        last_channel = groups.get(last_squad)
        return first_channel, last_channel
    except Exception as e:
        raise e


def notify(crash_name, user_name, first_build, last_build, first_squad, last_squad):
    channels = get_channels(first_squad, last_squad)
    payload = json.dumps({"channel": "#modi_test_crashes", "username": "Test Crashes", "text": message_content(crash_name, user_name, first_build, last_build, channels), "icon_emoji": ":ghost:"})
    url = 'https://hooks.slack.com/services/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'
    requests.post(url, data=payload)


def main():
    try:
        Fabric.fabric_login()
        Fabric.driver.get(modi_url)
        Fabric.wait_until_clickable_by('class name', 'Select-value-icon').click()
        crash_table = get_table_of_crashes()
        number_of_crashes = len(crash_table)
        while number_of_crashes > 0:
            crash_table = get_table_of_crashes()
            crash_info = get_crash_info(crash_table[number_of_crashes - 1])
            user_name = get_user(number_of_crashes)
            crash_name = crash_info[0]
            first_build, last_build = get_first_last_seen(crash_info)
            first_squad = extract_squad(first_build)
            last_squad = extract_squad(last_build)
            notify(crash_name, user_name, first_build, last_build, first_squad, last_squad)
            number_of_crashes -= 1
            Fabric.driver.get(modi_url)
            Fabric.wait_until_clickable_by('class name', 'Select-value-icon').click()
        Fabric.driver.quit()
    except Exception as e:
        Fabric.driver.quit()
        raise e


if __name__ == "__main__":
    main()
