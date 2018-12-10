import { Component, OnInit, OnDestroy } from '@angular/core';
import { StoreService } from '../../services';
import { groupBy as _groupBy } from 'lodash';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, OnDestroy {

  public patients = null;
  public patientsGrouped = null;

  public multiOpen;
  public dashTip1;
  public multi2Open;
  public multi3Open;

  public datepickerOptions = {
     relativeTop: '-368px',
   };

  public constructor(
    private store: StoreService,
  ) { }

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
      let groupedByStatus = _groupBy(res, (obj) => {
        return obj.status;
      });
      this.patientsGrouped = Object.assign({}, patientGroupDefaults, groupedByStatus);
    });
  }

  public ngOnDestroy() { }
}
