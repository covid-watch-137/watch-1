import { AfterViewChecked, AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService, NavbarService, StoreService, TimeTrackerService } from '../../../services';
import { AddConversationComponent } from './add-conversation/add-conversation.component';
import {
  map as _map,
  filter as _filter,
  find as _find,
  groupBy as _groupBy,
  uniqBy as _uniqBy,
} from 'lodash';
import * as moment from 'moment';
import { ModalService } from '../../../modules/modals';

@Component({
  selector: 'app-patient-messaging',
  templateUrl: './messaging.component.html',
  styleUrls: ['./messaging.component.scss'],
})
export class PatientMessagingComponent implements AfterViewChecked, OnDestroy, OnInit, AfterViewInit {

  public user = null;
  public patient = null;

  public messageStreams = [];
  public messageRecipients = [];
  public careTeam = {};
  public currentStream = null;

  public participants = {};

  public newMessageText:string = '';
  public userId:string = '';
  public planId:string = '';
  public scrolled = false;

  @ViewChild('chatBox') private chatBox: ElementRef;
  @ViewChild('imageUpload') private imageUpload: ElementRef;

  constructor(
    private auth: AuthService,
    private modals: ModalService,
    private nav: NavbarService,
    private route: ActivatedRoute,
    private router: Router,
    private store: StoreService,
    private timer: TimeTrackerService,
  ) { }


  public ngOnInit() {
    this.auth.user$.subscribe((user) => {
      if (!user) { return }
      this.user = user;
      this.userId = user.user.id;
      this.route.params.subscribe((params) => {
        this.planId = params.planId;
        this.nav.patientDetailState(params.patientId, params.planId);
        this.store.PatientProfile.read(params.patientId).subscribe(
          (patient) => {
            this.patient = patient;
            this.nav.addRecentPatient(this.patient);
          },
          (err) => {},
          () => {},
        );
        this.getCarePlan(params.planId).then((plan: any) => {
          this.timer.startTimer(this.user, plan);
        });

        this.store.CarePlan.detailRoute('GET', params.planId, 'care_team_members').subscribe(
          (res:any) => {
            res.forEach(m => {
              this.careTeam[m.employee_profile.user.id] = m.employee_profile;
            })

            this.store.CarePlan.detailRoute('GET', params.planId, 'message_recipients').subscribe(
              (res:any) => {
                this.messageRecipients = res.results;

                this.messageRecipients.forEach((m,i) => {
                  this.getMessageStreams(m, i, params.planId);
                })
                this.initRefreshInterval();
              }
            )
          }
        )

      });

    })
    this.scrollBottom();
  }

  public ngOnDestroy() {
    this.timer.stopTimer();
  }

  public getCarePlan(planId) {
    let promise = new Promise((resolve, reject) => {
      let carePlanSub = this.store.CarePlan.read(planId).subscribe(
        (carePlan) => resolve(carePlan),
        (err) => reject(err),
        () => {
          carePlanSub.unsubscribe();
        },
      );
    });
    return promise;
  }

  public getMessageStreams(m, i, planId) {
    this.store.CarePlan.detailRoute('GET', planId, `message_recipients/${m.id}/team_messages`).subscribe(
      (res:any) => {
        console.log(`stream ${i}`, m)
        this.messageStreams[i] = { id: m.id, participants: [], messages: [] };
        this.messageStreams[i].participants = _map(m.members, id => {
          if (this.careTeam[id]){
            return {
              id,
              firstName: this.careTeam[id] ? this.careTeam[id].user.first_name : '',
              lastName: this.careTeam[id] ? this.careTeam[id].user.last_name : '',
              title: this.careTeam[id] ? this.careTeam[id].title.abbreviation: '',
              isCurrentUser: id === this.userId,
            }
          } else if (id === this.patient.user.id) {
            return {
              id,
              firstName: this.patient.user.first_name,
              lastName: this.patient.user.last_name,
              title: 'Patient',
              isCurrentUser: false,
            }
          }
        })
        this.messageStreams[i].messages = _map(res.results, message => {
          return {
            text: message.content,
            image: message.image,
            userId: message.sender.id,
            date: message.created,
          }
        })
        if (i === 0) {
          this.currentStream = this.messageStreams[i];
        }
        setTimeout(() => {
          this.scrollBottom();
        }, 1000);
      }
    )

  }

  public refreshMessages(m, i, planId) {
    this.store.CarePlan.detailRoute('GET', planId, `message_recipients/${m.id}/team_messages`).subscribe(
      (res:any) => {
        this.messageStreams[i].messages = _map(res.results, message => {
          return {
            text: message.content,
            userId: message.sender.id,
            date: message.created,
          }
        })

      }
    );
  }

  public initRefreshInterval() {
    // setInterval(() => {
    //   this.messageRecipients.forEach((m,i) => {
    //     this.refreshMessages(m,i, this.planId);
    //   })
    // }, 5000)
  }

  public ngAfterViewInit() {
    this.scrollBottom();
  }

  public ngAfterViewChecked() {
//    this.scrollBottom('ngAfterViewChecked');
  }


  public scrollBottom() {
    this.chatBox.nativeElement.scrollTop = this.chatBox.nativeElement.scrollHeight + 64;
  }

  public getParticipants(stream) {
    if (stream) {
      const participants = _filter(stream.participants, p => !p.isCurrentUser);
      if (participants.length === 1) {
        const recipient = participants[0];
        return `${recipient.firstName} ${recipient.lastName}${recipient.title ? ', ' : ''}${recipient.title}`;
      }
      return _map(participants, p => p.lastName).join(', ');
    }
  }

  public getLastMessageTime(stream) {
    if (stream && stream.messages && stream.messages.length > 0) {
      const lastMessage = stream.messages[stream.messages.length - 1];
      return `${this.getDay(lastMessage)} at ${this.getTime(lastMessage)}`
    }
  }

  public changeStream(stream) {
    this.currentStream = _find(this.messageStreams, s => s.id === stream.id);
  }

  public messagesByDay(stream) {
    const grouped = _groupBy(stream.messages, m => moment(m.date).format('dddd'));
    const keys = Object.keys(grouped);
    return _map(keys, k => grouped[k]);
  }

  public getDay(message) {
    const date = moment(message.date);
    if (moment().diff(date, 'days') === 0) {
      return 'Today';
    } else if (moment().diff(date, 'days') === 1) {
      return 'Yesterday';
    } else if (moment().diff(date, 'days') <= 6) {
      return date.format('dddd');
    } else {
      return date.format('MM/DD/YY');
    }
  }

  public getTime(message) {
    return moment(message.date).format('h:mm A');
  }

  public getUser(stream, message) {
    return _find(stream.participants, p => p.id === message.userId);
  }

  public getNameAndTitle(user){
    return `${user.firstName} ${user.lastName}${user.title ? ', ' : ''}${user.title ? user.title : ''}`;
  }

  public isSelf(stream, message) {
    return this.getUser(stream, message).isCurrentUser;
  }

  public get currentUser() {
    if (this.currentStream) {
      return _find(this.currentStream.participants, p => p.isCurrentUser);
    }
    return null;
  }

  public addMessage() {

    this.store.CarePlan.detailRoute('POST', this.planId, `message_recipients/${this.currentStream.id}/team_messages`, {
      content: this.newMessageText,
    }).subscribe(
      (res:any) => {
        this.currentStream.messages.push({
          text: res.content,
          userId: res.sender.id,
          date: res.created,
        })
        this.scrollBottom();
      }
    )

    this.newMessageText = '';
  }

  public openAddConversation() {
    this.modals.open(AddConversationComponent, {
      AddConversationComponent,
      width: '440px',
      data: {
        planId: this.planId,
        userId: this.userId,
        careTeam: this.careTeam,
        patient: this.patient,
      }
    }).subscribe(res => {
      this.messageStreams.push({
        id: res.id,
        messages: [],
        participants: _map(res.members, id => {
          return {
            id,
            firstName: this.careTeam[id].user.first_name,
            lastName: this.careTeam[id].user.last_name,
            title: this.careTeam[id].title.abbreviation,
            isCurrentUser: id === this.userId,
          }
        })
      });
      this.currentStream = this.messageStreams[this.messageStreams.length -1];
    })
  }

  public processUpload() {
    const file : File = this.imageUpload.nativeElement.files[0];
    const reader = new FileReader;
    reader.readAsDataURL(file);
    reader.addEventListener('load', (event:any) => {
      this.store.CarePlan.detailRoute('POST', this.planId, `message_recipients/${this.currentStream.id}/team_messages`, {
        content: file.name,
        image: reader.result,
      }).subscribe((res:any) => {
        this.currentStream.messages.push({
          text: res.content,
          userId: res.sender.id,
          date: res.created,
          image: res.image,
        })
        this.scrollBottom();
      })
    })
  }
}
