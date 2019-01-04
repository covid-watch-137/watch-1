import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import  { Subject } from 'rxjs/Subject';
import 'rxjs/add/operator/debounceTime';
import 'rxjs/add/operator/distinctUntilChanged';
import { Subscription } from 'rxjs/Subscription';
import { PopoverOptions } from '../../modules/popover';
import { AuthService, NavbarService, StoreService } from '../../services';
import { ModalService, ConfirmModalComponent } from '../../modules/modals';
import patientsData from '../../routes/patients/active/patients-data.js';
import { filter as _filter } from 'lodash';

@Component({
  selector: 'app-nav',
  templateUrl: './nav.component.html',
  styleUrls: ['./nav.component.scss']
})
export class NavComponent implements OnDestroy, OnInit {

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
        let searchSub = this.store.PatientProfileSearch(searchStr).readListPaged().subscribe(
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
    this.getPatients().then((patients: any) => {
      patients = patientsData.results; // TODO: remove
      this.patients = patients;
      this.activePatientsCount = _filter(patients, p => p.is_active).length;
      this.invitedPatientsCount = _filter(patients, p => p.is_invited).length;
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
  }

  public confirmUnarchive() {
    this.modals.open(ConfirmModalComponent, {
      'backdrop': true,
      'closeDisabled': true,
      'width': '384px',
      'height': 'auto',
      'data': {
        'title': 'Unarchive Patient?',
        'body': 'This patient has been archived. Viewing this patient will unarchive them and change their status to inactive.',
        'okText': 'Continue',
        'cancelText': 'Cancel',
      }
    }).subscribe(() => {
    // do something with result
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

  public routeToPatient(patient) {
    this.router.navigate(['patient', patient.id]);
  }

  public getPatients() {
    let promise = new Promise((resolve, reject) => {
      let patientsSub = this.store.PatientProfile.readListPaged().subscribe(
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
}
