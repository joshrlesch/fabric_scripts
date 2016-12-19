import logging
import os

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from db_setup import TopCrashes, Base

from base_fabric import BaseFabric

logging.basicConfig(filename="crashlytics_scrape.log", level=logging.INFO)
engine = create_engine('sqlite:///fabric_scraping.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

Fabric = BaseFabric()

Fabric.fabric_login()

modi_versions = os.environ['MODI_VERSION']
hudroid_versions = os.environ['HUDROID_VERSION']


def get_link(bundle, version):
    if bundle == 'modi':
        url = "https://fabric.io/hudl5/ios/apps/com.hudl.{}/" \
              "issues?time=last-seven-days&event_type=crash&sub" \
              "Filter=state&state=open&cohort=new&build%5B0%5D={}".format(bundle, version)
        return url
    elif bundle == 'hudroid':
        url = "https://fabric.io/hudl5/android/apps/com.hudl.{}/" \
              "issues?time=last-seven-days&event_type=crash&subFilter=" \
              "state&state=open&cohort=new&build%5B0%5D={}%20%28{}%29".format(bundle, (version.split()[0]),
                                                                              (version.split()[1]))
        return url
    else:
        return ("NO URL ENTERED FOR {}".format(bundle))


def get_platform(bundles):
    if bundles == "modi":
        return 'iOS'
    else:
        return 'Android'


def seen(crash_info):
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


def versions():
    apps = {
        "modi": modi_versions.split(','),
        "hudroid": hudroid_versions.split(',')
    }
    return apps


apps = versions()
for bundles, versions in apps.items():
    for version in versions:
        print("Bundle: {}, Version: {}".format(bundles, version))
        Fabric.driver.get(get_link(bundles, version))
        try:
            Fabric.wait_until_visible_by('css selector', '.i_issue.open')
            crash_table = Fabric.driver.find_elements_by_css_selector(
                '.i_issue.open')
        except TimeoutException:
            print("NO CRASHES FOR {} {}".format(bundles, version))
            continue
        for crash in crash_table:
            crash_info = crash.__getattribute__('text').splitlines()
            number_of_notes = 0
            percent_rooted = None
            device = None
            os_version = None
            platform = get_platform(bundles)
            try:
                if crash.find_element_by_class_name('badges'):
                    link = crash.find_element_by_class_name(
                        'ellipsis').get_attribute('href')[17:]
                    loop = True
                    index = 1
                    while loop:
                        try:
                            icon = crash.find_element_by_xpath(
                                "//a[@href='{}']/../div[@class='badges']/div[{}]".
                                format(link, index))
                            icon_attribute = icon.get_attribute('data-hint')
                            if 'note' in icon_attribute:
                                number_of_notes = icon.text
                            elif 'Rooted' in icon_attribute:
                                percent_rooted = icon.text
                            elif 'Rooted' not in icon_attribute and 'iOS' not in icon_attribute and 'Android' not in icon_attribute and '%' in icon_attribute:
                                device = icon.text
                            elif 'Android' in icon_attribute or 'iOS' in icon_attribute:
                                os_version = icon.text
                            else:
                                pass
                                # print("NO ENTRY FOR BADGE TYPE")
                        except NoSuchElementException:
                            loop = False
                            # print("NO MORE BADGES")
                        index += 1
            except NoSuchElementException:
                pass
                # print("NO BADGES")
            first_seen, last_seen = seen(crash_info)
            try:
                crash_search = session.query(TopCrashes).filter(
                    TopCrashes.crash_subtitle == crash_info[1]).filter(
                        TopCrashes.app_version == version).one()
                crash_search.last_seen = last_seen
                crash_search.number_of_notes = number_of_notes
                crash_search.percent_rooted = percent_rooted
                crash_search.os_version = os_version
                crash_search.device = device
                crash_search.number_of_crashes = crash_info[len(crash_info) -
                                                            4]
                crash_search.number_of_users = crash_info[len(crash_info) - 2]
                session.commit()
                print("Updated Entry: {}".format(crash_info[0]))
            except NoResultFound:
                print("New Entry: {}".format(crash_info[0]))
                info_to_db = TopCrashes(
                    platform=platform,
                    app_version=version,
                    crash_name=crash_info[0],
                    crash_subtitle=crash_info[1],
                    first_seen=first_seen,
                    last_seen=last_seen,
                    number_of_notes=number_of_notes,
                    percent_rooted=percent_rooted,
                    os_version=os_version,
                    device=device,
                    number_of_crashes=crash_info[len(crash_info) - 4],
                    number_of_users=crash_info[len(crash_info) - 2])
                session.add(info_to_db)
                session.commit()

Fabric.driver.quit()
