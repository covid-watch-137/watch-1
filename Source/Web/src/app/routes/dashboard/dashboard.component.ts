import { Component, OnInit, OnDestroy } from '@angular/core';
import { StoreService, AuthService } from '../../services';
import { groupBy as _groupBy } from 'lodash';
import { PercentageGaugeComponent } from '../../components/graphs/percentage-gauge/percentage-gauge.component';
import { ActivePatientsGraphComponent } from '../../components/graphs/active-patients-graph/active-patients-graph.component';
import { PatientsEnrolledGraphComponent } from '../../components/graphs/patients-enrolled-graph/patients-enrolled-graph.component';
import * as moment from 'moment';
import { Subscription } from 'rxjs';
import patientsEnrolledData from './patientsEnrolledData';
import {
  find as _find
} from 'lodash';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, OnDestroy {

  public patients = null;
  public patientsGrouped = null;
  public employees = [];
  public employeeChecked = {};
  public facilities = [];
  public facilityChecked = {};

  public analyticsData = null;

  public patientsEnrolledData = patientsEnrolledData;
  public filteredPatientsEnrolledData = patientsEnrolledData;

  public multiOpen;
  public dashTip1;
  public multi2Open;
  public multi3Open;

  public patientsEnrolledStart:moment.Moment = moment().subtract(5, 'M').startOf('M');
  public patientsEnrolledEnd:moment.Moment = moment();

  public datepickerOptions = {
     relativeTop: '-368px',
   };

  public constructor(
    private auth: AuthService,
    private store: StoreService,
  ) { }

  private organizationSub:Subscription = null;

  public ngOnInit() {
    this.store.PatientProfile.readListPaged().subscribe((res) => {
      this.patients = res;
      let patientGroupDefaults = {
        'pre-potential': null,
        'potential': null,
        'invited': null,
        'delinquent': null,
        'inactive': null,
        'active': null,
      };
      let groupedByStatus = _groupBy(res, obj => {
        return obj.status;
      });
      this.patientsGrouped = Object.assign({}, patientGroupDefaults, groupedByStatus);
    });

    this.organizationSub = this.auth.organization$.subscribe(
      org => {
        if (!org) return;
        this.store.EmployeeProfile.readList().subscribe((res) => {
          this.employees = res.results;
          this.employees.forEach(employee => {
            this.employeeChecked[employee.id] = true;
          })
        })
        this.store.Facility.readList({
          organization_id: org.id,
        }).subscribe((res) => {
          this.facilities = res.results;
          this.facilities.forEach(facility => {
            this.facilityChecked[facility.id] = true;
          })
        })
        this.store.Organization.detailRoute('GET', org.id, 'dashboard_analytics').subscribe(
          res => {
            this.analyticsData = res;
          }
        )
      }
    )

    this.filterData();

  }

  public ngOnDestroy() { }

  get defaultDates():[moment.Moment, moment.Moment] {
    const end = moment();
    const startMonth = end.clone().subtract(5, 'M');
    const start = startMonth.startOf('M');
    return [start, end];
  }

  public toggleAllFilterList(list:any, state:boolean) {
    const keys = Object.keys(list);
    keys.forEach(key => {
     list[key] = state;
    })
  }

  public toggleAllUsers(state:boolean) {
    return this.toggleAllFilterList(this.employeeChecked, state);
  }

  public toggleAllFacilities(state:boolean) {
    return this.toggleAllFilterList(this.facilityChecked, state);
  }

  public filterData() {
    this.filteredPatientsEnrolledData = this.patientsEnrolledData
      .slice(
        this.patientsEnrolledData.indexOf(
          _find(this.patientsEnrolledData, d => d.month === this.patientsEnrolledStart.format('MMMM, YYYY'))
        ),
        this.patientsEnrolledData.indexOf(
          _find(this.patientsEnrolledData, d => d.month === this.patientsEnrolledEnd.format('MMMM, YYYY'))
        ),
      );
  }

}
