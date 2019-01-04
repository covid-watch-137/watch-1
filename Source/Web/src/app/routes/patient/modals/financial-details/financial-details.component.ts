import { Component, OnInit } from '@angular/core';
import { find as _find } from 'lodash';

@Component({
  selector: 'app-financial-details',
  templateUrl: './financial-details.component.html',
  styleUrls: ['./financial-details.component.scss'],
})
export class FinancialDetailsComponent implements OnInit {

  public data = null;

  public selectedPlanType = 'CoCM';
  public billingTypes = [
    {
      name: 'Psychiatric Collaborative Care Management',
      abr: 'CoCM',
      cpt: [
        {
          code: 99492,
          text: '70 minutes per month of care for first month of care plan',
        },
        {
          code: 99493,
          text: '60 minutes of care call months after the first month of care',
        },
        {
          code: 99494,
          text: 'Each additional 30 minutes of care per calendar month',
        }
      ],
    },
    {
      name: 'Remote Patient Management',
      abr: 'RPM',
      cpt: [
        {
          code: 99091,
          text: 'Bill for 30 minutes of reviewing patient health data per month',
        },
      ],
    },
    {
      name: 'Behavioral Health Integration',
      abr: 'BHI',
      cpt: [
        {
          code: 99484,
          text: 'At least 20 minutes per month of behavioral health care by the care provider',
        },
      ],
    },
    {
      name: 'Chronic Care Management',
      abr: 'CCM',
      cpt: [
        {
          code: 99490,
          text: '20 minutes of clinical staff time per month directed by the physician or qualified staff',
        }
      ],
    },
    {
      name: 'Complex Chronic Care Management',
      abr: 'CCCM',
      cpt: [
        {
          code: 99487,
          text: '60 minutes of clinical staff time per month directed by physician or qualified staff',
        }
      ]
    },
    {
      name: 'Transitional Care Management',
      abr: 'TCM',
      cpt: [
        {
          code: 99495,
          text: 'TCM services with moderate medical decision making complexity.'
        },
        {
          code: 99496,
          text: 'TCM services with moderate medical decision making complexity.'
        }
      ]
    }
  ]

  constructor() {

  }

  public ngOnInit() {
    console.log(this.data);
  }

  get carePlanFull() {

    const fullPlanNames = {
      CoCM: 'Psychiatric Collaborative Care Management',
      RPM: 'Remote Patient Management',
      BHI: 'Behavioral Health Initiative',
      CCM: 'Chronic Care Management',
      CCCM: 'Complex Chronic Care Management',
      TCM: 'Transitional Care Management',
    }

    if (this.data && this.data.carePlan) {
      return fullPlanNames[this.data.carePlan] || '';
    }
  }

  public billingTypeByAbr(abr) {
    return _find(this.billingTypes, t => t.abr === abr);
  }

}
