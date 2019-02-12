import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import  { Subject } from 'rxjs/Subject';
import 'rxjs/add/operator/debounceTime';
import 'rxjs/add/operator/distinctUntilChanged';
import { Subscription } from 'rxjs/Subscription';
import { PopoverOptions } from '../../modules/popover';
import { AuthService, NavbarService, StoreService } from '../../services';
import { ModalService, ConfirmModalComponent } from '../../modules/modals';
import {
  filter as _filter,
  map as _map,
  sum as _sum
} from 'lodash';
import tasksData from './tasksData';
import * as moment from 'moment';

@Component({
  selector: 'app-nav',
  templateUrl: './nav.component.html',
  styleUrls: ['./nav.component.scss']
})
export class NavComponent implements OnDestroy, OnInit {

  public moment = moment;

  public employee = null;
  public organization = null;
  public organizations = [];
  public patients = [];
  public activePatientsCount = 0;
  public inactivePatientsCount = 0;
  public invitedPatientsCount = 0;
  public potentialPatientsCount = 0;
  public selectableOrganizations = [];
  public appListOpen = false;
  public appListOptions: PopoverOptions = {
    relativeBottom: '0',
    relativeLeft: '1.5rem',
  };
  public searchOpen = false;
  public searchString = '';
  public taskDropOpen = false;
  public taskDropOptions: PopoverOptions = {
    relativeRight: '16rem',
  };
  public notificationsDropOpen = false;
  public notificationsDropOptions: PopoverOptions = {
    relativeRight: '30rem',
  };
  public logoutOpen = false;
  public logoutDropOptions: PopoverOptions = {
    relativeRight: '16rem',
  };
  public patientsDropOpen = false;
  public patientsDropOptions: PopoverOptions = {
    relativeBottom: '0',
    relativeLeft: '0',
  };

  public searchResults = [];
  public searchUpdated$: Subject<string> = new Subject<string>();

  public normalState = true;
  public planDetailState = false;
  public patientDetailState = false;

  private authSub: Subscription = null;
  private organizationSub: Subscription = null;
  private routeParams = null;

  public notifications = [];
  public tasksData = tasksData;
  public tasks = [];

  constructor(
    private router: Router,
    private auth: AuthService,
    public nav: NavbarService,
    private store: StoreService,
    private modals: ModalService,
  ) { }

  public ngOnInit() {
    this.authSub = this.auth.user$.subscribe(
      (res) => {
        this.employee = res;
      },
      (err) => {},
      () => {}
    );
    this.organizationSub = this.auth.organization$.subscribe(
      (res) => {
        if (res === null) {
          return;
        }
        this.organization = res;
        this.store.Organization.readListPaged()
          .subscribe(
            (res) => {
              this.organizations = res;
              this.selectableOrganizations = this.organizations.filter((obj) => {
                return obj.id !== this.organization.id;
              });
            },
            () => {},
            () => {},
          );
      },
      (err) => {},
      () => {}
    );
    this.searchUpdated$
      .asObservable()
      .debounceTime(400)
      .distinctUntilChanged()
      .subscribe((searchStr) => {
        if (searchStr.length < 3) {
          this.searchResults = [];
          this.searchOpen = false;
          return;
        }
        let searchSub = this.store.PatientProfile.listRoute('get', 'search', {}, {
          q: searchStr,
        }).subscribe(
          (searchResults: any) => {
            this.searchResults = searchResults;
            if (this.searchResults.length > 0) {
              this.searchOpen = true;
            }
          },
          (err: any) => {},
          () => {
            searchSub.unsubscribe();
          },
        );
      });

    this.patients = [];
    this.getPatientsOverview().then((patientOverview: any) => {
      this.patients = patientOverview;
      this.activePatientsCount = patientOverview.active;
      this.inactivePatientsCount = patientOverview.inactive;
      this.potentialPatientsCount = patientOverview.potential;
      this.invitedPatientsCount = patientOverview.invited;
    });

    this.getNotifications().then((notifications:any) => {
      this.notifications = notifications.results;
    });
    this.getTasks().then((tasks:any) => {
      this.tasks = tasks;
    });
  }

  public ngOnDestroy() {
    if (this.authSub) {
      this.authSub.unsubscribe();
    }
    if (this.organizationSub) {
      this.organizationSub.unsubscribe();
    }
  }

  public logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  public switchOrganization(organization) {
    this.auth.switchOrganization(organization.id);
    this.router.navigate(['/dashboard']);
  }

  public confirmUnarchive() {
    this.modals.open(ConfirmModalComponent, {
      backdrop: true,
      closeDisabled: true,
      width: '384px',
      height: 'auto',
      data: {
        'title': 'Unarchive Patient?',
        'body': 'This patient has been archived. Viewing this patient will unarchive them and change their status to inactive.',
        'okText': 'Continue',
        'cancelText': 'Cancel',
      }
    }).subscribe(() => {

    });
  }

  public closeAllPopovers() {
    this.appListOpen = false;
    this.searchOpen = false;
    this.taskDropOpen = false;
    this.notificationsDropOpen = false;
    this.logoutOpen = false;
    this.patientsDropOpen = false;
  }

  public searchChange(value: string) {
    this.searchUpdated$.next(value);
  }

  public routeToProfile() {
    this.router.navigate(['/user', this.employee.id]);
  }

  public routeToPatients() {
    this.router.navigate(['/patients/active']);
  }

  public routeToPatient(patient) {
    this.router.navigate(['/patient', patient.id]);
  }

  public routeToPatientPage(route) {
    this.router.navigate(['/patient', this.nav.patientDetailId, route, this.nav.patientPlanId]);
  }

  public getPatientsOverview() {
    let promise = new Promise((resolve, reject) => {
      let patientsSub = this.store.PatientProfile.detailRoute('GET', '', 'overview').subscribe(
        (patients) => {
          resolve(patients);
        },
        (err) => {
          reject(err);
        },
        () => {
          patientsSub.unsubscribe();
        }
      );
    });
    return promise;
  }

  private getNotifications() {
    return new Promise((resolve, reject) => {
      this.auth.user$.subscribe(
        user => {
          if (!user) return;
          let notificationsSub = this.store.User.detailRoute('GET', user.user.id, 'notifications').subscribe(
            (notifications:any) => {
              resolve(notifications);
            }
          )
        }
      )
    });
  }

  public get notificationData() {
    if (this.notifications.length) {
      return [
        {
          category: 'Unread Messages',
          notifications: _filter(this.notifications, n => n.category === 'unread_message'),
        },
        {
          category: 'Flagged Patients',
          notifications: _filter(this.notifications, n => n.category === 'flagged_patient'),
        },
        {
          category: 'Assignments',
          notifications: _filter(this.notifications, n => n.category === 'assignment'),
        }
      ];
    }
  }

  private getTasks() {
    return new Promise((resolve, reject) => {
      let tasksSub = this.store.TeamTask.readListPaged().subscribe(
        tasks => {
          resolve(tasks);
        }
      )
    });
  }

  public routeToAnalytics() {
    window.open('https://www.google.com', '_self');
  }

  public get taskCount() {
    return tasksData.checkIns.length + tasksData.tasks.length;
  }

  public timeSince(d) {
    const date = moment(d);
    const daysSince = moment().diff(date, 'days');
    const hoursSince = moment().diff(date, 'hours');
    const minutesSince = moment().diff(date, 'minutes');

    if (!daysSince) {
      if (!hoursSince) {
        return `${minutesSince} minute${minutesSince !== 1 ? 's' : ''} ago`;
      } else {
        return `${hoursSince} hour${hoursSince !== 1 ? 's' : ''} ago`;
      }
    } else {
      return `${daysSince} day${daysSince !== 1 ? 's' : ''} ago`;
    }
  }
}
