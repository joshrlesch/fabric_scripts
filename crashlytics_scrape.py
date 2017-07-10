import os
import time
import json

from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from db_setup import TopCrashes, Base

from base_fabric import BaseFabric

engine = create_engine('sqlite:///{}'.format(os.environ['DB_LOCATION']))
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

Fabric = BaseFabric()

modi_versions = os.environ['MODI_VERSION']
hudroid_versions = os.environ['HUDROID_VERSION']


def get_url_for_crash(crash, link_index):
    try:
        return crash.find_element_by_xpath(
            "//tbody[@class='bg-white']/tr[{}]/td[2]/a".format(
                link_index)).get_attribute('href')[17:]
    except StaleElementReferenceException as e:
        print("[get_url_for_crash] Stale Element: {}".format(e))


def url_for_bundle_and_version(bundle, version):
    if bundle == 'modi':
        return "https://fabric.io/hudl5/ios/apps/com.hudl.{}/" \
              "issues?time=last-seven-days&event_type=crash&sub" \
              "Filter=state&state=open&cohort=new&build%5B0%5D={}".format(bundle, version.split()[0])
    else:
        return "https://fabric.io/hudl5/android/apps/com.hudl.{}/" \
              "issues?time=last-seven-days&event_type=crash&subFilter=" \
              "state&state=open&cohort=new&build%5B0%5D={}%20%28{}%29".format(bundle, (version.split()[0]),
                                                                              (version.split()[1]))


def get_platform(bundles):
    if bundles == "modi":
        return 'iOS'
    else:
        return 'Android'


def get_bundles_and_versions():
    bundle_version_dict = {
        "modi": modi_versions.split(','),
        "hudroid": hudroid_versions.split(',')
    }
    return bundle_version_dict


def get_crash_rate():
    Fabric.wait_until_visible_by('class name', 'crash-free-percent')
    try:
        return str(
            Fabric.driver.find_element_by_xpath(
                "//div[@class='issues_metrics']/div[1]/div/span/div[2]/div/div/span"
            ).text)
    except StaleElementReferenceException as e:
        print("[crash_rate] Stale Element: {}".format(e))


def get_table_of_crashes():
    try:
        Fabric.wait_until_visible_by('css selector', '.i_issue.open')
        try:
            return Fabric.driver.find_elements_by_css_selector('.i_issue.open')
        except StaleElementReferenceException as e:
            print("[get_table_of_crashes] Stale Element: {}".format(e))
    except TimeoutException:
        print("[get_table_of_crashes] No crashes for current version.")


def get_crash_info(crash):
    try:
        return crash.__getattribute__('text').splitlines()
    except StaleElementReferenceException as e:
        print("[crash_info] Stale element: {}".format(e))


def create_empty_dict():
    return {
        'name': None,
        'subtitle': None,
        'version': None,
        'first_seen': None,
        'last_seen': None,
        'notes': 0,
        'rooted': None,
        'os_version': None,
        'device': None,
        'crashes': None,
        'users': None,
        'crash_rate': None,
        'current_time': None
    }


def get_icons_if_any(crash, crash_info, link_index, crash_data_dict):
    if check_crash_for_icons(crash):
        link = get_url_for_crash(crash, link_index)
        if link:
            loop = True
            icon_index = 1
            while loop:
                try:
                    crash_data_dict = get_crash_icons(crash, link, icon_index,
                                                      crash_data_dict)
                except NoSuchElementException:
                    loop = False
                    print("[main] No more badges for crash {}".format(
                        crash_info[0]))
                except StaleElementReferenceException:
                    print("[main] Stale element when looping for icons.")
                    loop = False
                except Exception:
                    if icon_index > 1:
                        print("[main] No more icons for crash {}".format(
                            crash_info[0]))
                    else:
                        print("[main] No icons for crash {}".format(
                            crash_info[0]))
                    loop = False
                icon_index += 1
        else:
            print("[main] Link was a stale element.")
    else:
        print("[main] No icons for crash {}.".format(crash_info[0]))
    return crash_data_dict


def check_crash_for_icons(crash):
    try:
        return crash.find_element_by_class_name('badges')
    except NoSuchElementException:
        print("[icons] No icons for crash.")
        return False
    except StaleElementReferenceException:
        print("[icons] Stale icon.")
        return False


def get_icon(crash, link, icon_index):
    try:
        return crash.find_element_by_xpath(
            "//a[@href='{}']/../div[@class='badges']/div[{}]".format(
                link, icon_index))
    except NoSuchElementException:
        print("[get_icon] No icon for index {}.".format(icon_index))


def get_crash_icons(crash, link, icon_index, crash_data_dict):
    icon = get_icon(crash, link, icon_index)
    icon_attribute = icon.get_attribute('data-hint')
    if 'note' in icon_attribute:
        crash_data_dict['notes'] = icon.text
        print("[get_crash_icons] NOTES: = {}".format(crash_data_dict['notes']))
    elif 'Rooted' in icon_attribute:
        crash_data_dict['rooted'] = icon.text
        print("[get_crash_icons] PERCENT ROOTED = {}".format(
            crash_data_dict['rooted']))
    elif 'Rooted' not in icon_attribute and 'iOS' not in icon_attribute and 'Android' not in icon_attribute and '%' in icon_attribute:
        crash_data_dict['device'] = icon.text
        print(
            "[get_crash_icons] DEVICE = {}".format(crash_data_dict['device']))
    elif 'Android' in icon_attribute or 'iOS' in icon_attribute:
        crash_data_dict['os_version'] = icon.text
        print("[get_crash_icons] OS VERSION = {}".format(
            crash_data_dict['os_version']))
    else:
        pass
    return crash_data_dict


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
    return first_seen, last_seen


def update_crash_in_db(crash_search, crash_data_dict):
    print("[update_crash_in_db] crash_data_dict: {})".format(crash_data_dict))
    crash_search.last_seen = crash_data_dict['last_seen']
    crash_search.number_of_notes = crash_data_dict['notes']
    crash_search.percent_rooted = crash_data_dict['rooted']
    crash_search.os_version = crash_data_dict['os_version']
    crash_search.device = crash_data_dict['device']
    crash_search.number_of_crashes = crash_data_dict['crashes']
    crash_search.number_of_users = crash_data_dict['users']
    crash_search.crash_rate = crash_data_dict['crash_rate']
    crash_search.run_time = crash_data_dict['current_time']
    session.commit()
    print("[updated_entry] Updated Entry: {}".format(crash_data_dict['name']))


def add_crash_to_db(crash_data_dict):
    info_to_db = TopCrashes(
        platform=crash_data_dict['platform'],
        app_version=crash_data_dict['version'],
        crash_name=crash_data_dict['name'],
        crash_subtitle=crash_data_dict['subtitle'],
        first_seen=crash_data_dict['first_seen'],
        last_seen=crash_data_dict['last_seen'],
        number_of_notes=crash_data_dict['notes'],
        percent_rooted=crash_data_dict['rooted'],
        os_version=crash_data_dict['os_version'],
        device=crash_data_dict['device'],
        number_of_crashes=crash_data_dict['crashes'],
        number_of_users=crash_data_dict['users'],
        crash_rate=crash_data_dict['crash_rate'],
        run_time=crash_data_dict['current_time'])
    session.add(info_to_db)
    session.commit()


def save_to_file(crash_data_dict):
    crash_data = json.dumps(crash_data_dict)
    with open('crashes.json', 'a') as file:
        file.write(crash_data + '\n')


def delete_file(file):
    try:
        os.remove(file)
    except FileNotFoundError as e:
        print(e)


def main():
    try:
        bundles_and_versions = get_bundles_and_versions()
        Fabric.fabric_login()
        for bundles, versions in bundles_and_versions.items():
            for version in versions:
                print(
                    "[main] Bundle: {}, Version: {}".format(bundles, version))
                Fabric.driver.get(url_for_bundle_and_version(bundles, version))
                time.sleep(2)
                crash_table = get_table_of_crashes()
                link_index = 1
                for crash in crash_table:
                    crash_data_dict = create_empty_dict()
                    crash_info = get_crash_info(crash)
                    crash_data_dict['current_time'] = int(time.time())
                    crash_data_dict['platform'] = get_platform(bundles)
                    crash_data_dict['version'] = version
                    crash_data_dict['name'] = crash_info[0]
                    crash_data_dict['subtitle'] = crash_info[1]
                    crash_data_dict['crashes'] = crash_info[len(crash_info) -
                                                            4]
                    crash_data_dict['users'] = crash_info[len(crash_info) - 2]
                    crash_data_dict['crash_rate'] = get_crash_rate()
                    crash_data_dict['first_seen'], crash_data_dict[
                        'last_seen'] = get_first_last_seen(crash_info)
                    crash_data_dict = get_icons_if_any(
                        crash, crash_info, link_index, crash_data_dict)
                    try:
                        crash_search = session.query(TopCrashes).filter(
                            TopCrashes.crash_subtitle ==
                            crash_data_dict['subtitle']).filter(
                                TopCrashes.app_version == crash_data_dict[
                                    'version']).one()
                        update_crash_in_db(crash_search, crash_data_dict)
                        save_to_file(crash_data_dict)
                    except NoResultFound:
                        add_crash_to_db(crash_data_dict)
                        save_to_file(crash_data_dict)
                    link_index += 1
        Fabric.driver.quit()
    except Exception as e:
        Fabric.driver.quit()
        raise e


if __name__ == "__main__":
    main()
