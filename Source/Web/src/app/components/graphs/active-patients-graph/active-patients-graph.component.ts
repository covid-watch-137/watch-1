import { Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import * as d3 from 'd3';
import {
  map as _map,
  sum as _sum
} from 'lodash';

@Component({
  selector: 'app-active-patients-graph',
  templateUrl: './active-patients-graph.component.html',
  styleUrls: ['./active-patients-graph.component.scss']
})
export class ActivePatientsGraphComponent implements OnInit {

  @ViewChild('chart') private chartContainer: ElementRef;

  private _data = null;

  constructor() { }

  @Input()
  public get data() {
    return this._data;
  }

  public set data(percent) {
    this._data = percent;
    this.drawChart();
  }

  ngOnInit() {
    this.drawChart();
  }

  private drawChart() {
    if (!this.data) return;
    class PatientData {
      name: string;
      value: number;
      color: string;
    }
    var data = [
      {name: "On Track", value: this.data.on_track, color: '#4caf50' },
      {name: "Low Risk", value: this.data.low_risk, color: '#ff9800' },
      {name: "Med Risk", value: this.data.med_risk, color: '#f44336' },
      {name: "High Risk", value: this.data.high_risk, color: '#880e4f' },
    ];

    const total = _sum(_map(data, d => d.value));

    var width = 450;
    var height = 450;
    var thickness = 26;

    var radius = Math.min(width, height) / 2;

    let element = this.chartContainer.nativeElement;
    element.innerHTML = '';
    var svg = d3.select(element)
    .append('svg')
    .attr('class', 'pie')
    .attr('width', width)
    .attr('height', height);

    var g = svg.append('g')
    .attr('transform', 'translate(' + (width/2) + ',' + (height/2) + ')');

    var arc = d3.arc()
    .innerRadius(radius - thickness)
    .outerRadius(radius);

    var pie = d3.pie<void, PatientData>()
    .value(function(d:any) { return d.value; })
    .sort(null)
    .padAngle(.02)

    var path = g.selectAll('path')
    .data(pie(data))
    .enter()
    .append("g")
      .append('path')
      .attr('d', <any>arc)
      .attr('fill', (d:any) => d.data.color)
      .attr('stroke')

    g.append('text')
      .attr('class', 'radial-progress__text')
      .attr('fill', '#ffffff')
      .attr('text-anchor', 'middle')
      .attr('dy', '-.5rem')
      .style('font-size', '4rem')
      .style('font-weight', 100)
      .text(total);

    g.append('text')
      .attr('class', 'radial-progress__text')
      .attr('fill', '#ffffff')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.5rem')
      .style('font-size', '2rem')
      .style('font-weight', 100)
      .text('active patients');


  }

}
