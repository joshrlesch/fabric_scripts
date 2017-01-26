from datetime import datetime
from time import sleep

import requests
import logging

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from db_setup import ReleaseSummary, Base

from base_fabric import BaseFabric
from base_fabric import LocatorType

try:
    logging.basicConfig(filename="beta_stats.log", level=logging.INFO)
    engine = create_engine('sqlite:///fabric_scraping.db')
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    Fabric = BaseFabric()

    branch_names = []
    for org in Fabric.ORG.split():
        open_pulls = requests.get("https://api.github.com/repos/{}/pulls?sort=updated&per_page=100&access_token={}".format(org, Fabric.TOKEN)).json()

        for pull in open_pulls:
            new_dict = {'branch_name': pull['head']['ref'],
                        'created_at': pull['created_at'],
                        'updated_at': pull['updated_at'],
                        'closed_at': pull['closed_at'],
                        'merged_at': pull['merged_at'],
                        'number': pull['number']
                        }
            branch_names.append(new_dict)


    Fabric.fabric_login()

    # Get list of urls for specific branch
    # {"<app name>" : "<fabric beta url for that app"}
    apps = {}

    for app, url in apps.items():
        Fabric.driver.get(url)

        try:
            Fabric.wait_until_clickable_by(LocatorType.XPATH, '//*[@id="l_dashboard"]/aside/div/div/div/div[2]/div[6]/div[1]/div/i').click()
        except TimeoutException:
            pass

        for branch in branch_names:
            try:
                search_box = Fabric.driver.find_element_by_xpath("//input[@placeholder='Search Builds']")
            except NoSuchElementException:
                Fabric.wait_until_clickable_by(LocatorType.CLASS_NAME, "beta_distribution").click()
                search_box = Fabric.driver.find_element_by_xpath("//input[@placeholder='Search Builds']")

            if not search_box.is_displayed():
                Fabric.wait_until_visible_by(LocatorType.CLASS_NAME, "distributed-at")
                Fabric.wait_until_clickable_by(LocatorType.CSS_SELECTOR, ".release-picker-container").click()

                Fabric.wait_until_clickable_by(LocatorType.XPATH, "//input[@placeholder='Search Builds']").clear()

                Fabric.wait_until_clickable_by(LocatorType.XPATH, "//input[@placeholder='Search Builds']").send_keys(branch['branch_name'])
            sleep(1)

            build_links = []
            for link in Fabric.driver.find_elements_by_xpath("//div[@class='releases']/a"):
                build_links.append(link.get_attribute('href'))

            data = []

            for link in build_links:
                Fabric.driver.get(link)

                sessions = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[1]/div[1]/div/div/div[1]').text
                time_tested = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div/div[1]').text
                time_unit = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div/div[2]').text
                crash_free_devices = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/div/div[1]').text
                crash_free_sessions = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[2]/div[2]/div/div[1]/div/div[1]').text
                devices = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[2]/div/div/div[1]/div[1]').text
                crashed = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div[2]/div/div/div[2]/div[1]').text
                sessions_crashed = Fabric.wait_until_clickable_by(LocatorType.XPATH,
                    '//*[@id="l_dashboard"]/article/div[1]/aside/div/div/div[2]/div[2]/div/div[2]/div[2]/div/div[2]/div/div/div[2]/div[1]').text

                hours = 0
                minutes = 0
                seconds = 0
                minutes_tested = 0
                seconds_tested = 0

                if time_unit == "HOURS TESTED":
                    # 4:34 hours:minutes
                    hours, minutes = time_tested.split(":")
                else:
                    # 24:33 minutes:seconds
                    # 0:23 minutes:seconds
                    minutes, seconds = time_tested.split(":")

                minutes_tested += (int(hours) * 60) + int(minutes)
                seconds_tested += (int(minutes_tested) * 60) + int(seconds)

                logging.info("app-{} branch-{}; session-{}; time_tested-{}; crash_free_devices-{}; crash_free_sessions-{}; devices-{}; crashed-{}; sessions_crashed-{}".format(
                    app,
                    branch,
                    sessions,
                    seconds_tested,
                    crash_free_devices,
                    crash_free_sessions,
                    devices,
                    crashed,
                    sessions_crashed))

                data.append({"sessions": int(sessions),
                            "time_tested": int(seconds_tested),
                            "devices": int(devices),
                            "crashed": int(crashed),
                            "sessions_crashed": int(sessions_crashed),
                            "link": link})

            sessions = 0
            total_time = 0
            crash_free_devices = 0
            crash_free_sessions = 0
            devices = 0
            crashed = 0
            sessions_crashed = 0

            for d in data:
                sessions += d['sessions']
                total_time += d['time_tested']

                devices += d['devices']
                crashed += d['crashed']
                sessions_crashed += d['sessions_crashed']

            if devices > 0:
                crash_free_devices = ((devices - crashed) / devices)
            if sessions > 0:
                crash_free_sessions = ((sessions - sessions_crashed) / sessions)

            # search db for branch name
            try:
                branch_search = session.query(ReleaseSummary).filter(
                    ReleaseSummary.branch == branch['branch_name']).filter(
                    ReleaseSummary.app == app).one()
            except NoResultFound:
                branch_search = None

            if branch_search:
                # if it's there, check to see if total_time is greater and then upcert db entry
                if branch_search.total_time < total_time:
                    print("Updating db entry: {}".format(branch['branch_name']))
                    branch_search.sessions = sessions
                    branch_search.crash_free_devices = "{:.1%}".format(crash_free_devices)
                    branch_search.crash_free_sessions = "{:.1%}".format(crash_free_sessions)
                    branch_search.devices = devices
                    branch_search.crashed = crashed
                    branch_search.sessions_crashed = sessions_crashed
                    branch_search.total_time = total_time
                    branch_search.pr_created_at = datetime.strptime(branch['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    branch_search.pr_updated_at = datetime.strptime(branch['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                    session.commit()
            else:
                # else insert new entry if there are builds pushed to fabric
                if len(build_links) >= 1:
                    print("Inserting new branch: {}".format(branch['branch_name']))
                    insert_branch = ReleaseSummary(app=app,
                                                branch=branch['branch_name'],
                                                sessions=sessions,
                                                total_time=total_time,
                                                crash_free_devices="{:.1%}".format(crash_free_devices),
                                                crash_free_sessions="{:.1%}".format(crash_free_sessions),
                                                devices=devices,
                                                crashed=crashed,
                                                sessions_crashed=sessions_crashed,
                                                pr_number=branch['number'],
                                                pr_created_at=datetime.strptime(branch['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                                                pr_updated_at=datetime.strptime(branch['updated_at'], '%Y-%m-%dT%H:%M:%SZ'))
                    session.add(insert_branch)
                    session.commit()

    stored_prs = session.query(ReleaseSummary.pr_number).distinct().all()

    prs_in_sql = []
    for b in stored_prs:
        prs_in_sql.append(b.pr_number)

    prs_in_github = []
    for b in branch_names:
        prs_in_github.append(b['number'])

    missing_prs = set(prs_in_sql) - set(prs_in_github)

    for pr in missing_prs:
        for row in session.query(ReleaseSummary).filter(ReleaseSummary.pr_number == pr).filter(ReleaseSummary.pr_closed_at == None).all():
            print("PR was closed or merged: {}".format(row.branch))
            closed_pulls = requests.get(
                "https://api.github.com/repos/{}/pulls/{}?access_token={}".format(Fabric.ORG,
                    row.pr_number,
                    Fabric.TOKEN)).json()
            row.pr_updated_at = datetime.strptime(closed_pulls['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            row.pr_closed_at = datetime.strptime(closed_pulls['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
            if closed_pulls['merged_at']:
                row.pr_merged_at = datetime.strptime(closed_pulls['merged_at'], '%Y-%m-%dT%H:%M:%SZ')
        session.commit()

    Fabric.driver.quit()
except Exception as e:
    Fabric.driver.quit()
    raise e

