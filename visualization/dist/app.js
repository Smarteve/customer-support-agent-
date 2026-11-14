'use strict';

const concepts = window.CONCEPTS;
const conceptById = Object.fromEntries(concepts.map(c => [c.id, c]));
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const vaultName = 'Obsidian Vault';
const notebook = 'AI Customer Support Engine';
const obsidianURI = (file, concept = false) => `obsidian://open?vault=${encodeURIComponent(vaultName)}&file=${encodeURIComponent(`${notebook}/${concept ? 'Concepts/' : ''}${file}`)}`;
const chip = id => `<button class="concept-chip" data-concept="${id}">${escapeHTML(conceptById[id].title)} ↗</button>`;
let toastTimer;
function toast(message) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3500); }

const components = [
  {id:'customer',no:'01',title:'Event Source / Simulator',sub:'Sends to our webhook endpoint',x:35,y:40,type:'external',tech:'HTTP webhook · stable event identity',description:'We own the receiving FastAPI endpoint. An external platform or customer backend usually sends the webhook. The local simulator replaces that sender and records mock replies.',does:['Send signed customer messages','Reuse the event ID for a retry','Receive the simulated final response'],rule:'A repeated event must not create another logical run.',concepts:['events','webhooks','idempotency']},
  {id:'gateway',no:'02',title:'FastAPI',sub:'Webhooks + Status API',x:370,y:40,type:'service',tech:'One service · webhook, REST, and SSE routes',description:'FastAPI saves input before RQ submission. For live progress, it subscribes to Redis Pub/Sub. A notice triggers a read of saved PostgreSQL events and an SSE update to React. Connection replay recovers missed notices.',does:['Save input before submitting an RQ job','Subscribe to Redis progress notices','Replay saved events and send SSE updates'],rule:'Database commit and queue submission are separate. A crash between them leaves retryable pending work.',concepts:['lifecycle','webhooks','pubsub','sse']},
  {id:'dashboard',no:'08',title:'React Dashboard',sub:'Status + execution timeline',x:705,y:40,type:'external',tech:'REST commands · SSE subscription',description:'The dashboard opens an SSE subscription to FastAPI. Redis notices trigger live delivery of saved PostgreSQL events. On reconnect, the API replays events after the browser’s last sequence.',does:['Display current state from the runs table','Append ordered entries from run_events','Request approval or an authorized retry'],rule:'Live path: Worker → Redis Pub/Sub → FastAPI SSE → Dashboard.',concepts:['lifecycle','sse','observability']},
  {id:'database',no:'03',title:'PostgreSQL',sub:'Current state + saved events',x:705,y:220,type:'storage',tech:'runs · run_events · messages · results',description:'PostgreSQL stores input, state, and ordered run history. The worker commits each step before publishing its Redis notice. FastAPI reads saved rows on a notice or reconnect. Pub/Sub does not replace this history.',does:['Store event and pending run together','Save state and history events atomically','Keep results available after a restart'],rule:'Commit first. Publish second. Replay saved events after a disconnect.',concepts:['lifecycle','recovery','sse']},
  {id:'queue',no:'04',title:'Redis',sub:'RQ queue + Pub/Sub channel',x:370,y:220,type:'service',tech:'One deployment · two separate roles',description:'RQ holds job references for worker execution. Pub/Sub broadcasts progress notices to subscribed FastAPI processes. These interfaces use the same Redis deployment. Notices do not form a durable event history.',does:['RQ: schedule saved run IDs','Pub/Sub: broadcast committed progress notices','Notify each subscribed FastAPI process'],rule:'RQ schedules work. Pub/Sub signals live updates. PostgreSQL keeps history.',concepts:['queue','pubsub','lifecycle']},
  {id:'agent',no:'05',title:'Agent Worker',sub:'Model loop + checked tools',x:370,y:400,type:'service',tech:'RQ entry point → async runtime',description:'The worker checks tools and executes the bounded model loop. It commits state and a history event for each step, then publishes a small Redis notice. A notification failure must not repeat the business action.',does:['Check access, arguments, and policy','Commit start, progress, and final outcome','Publish run ID and sequence after commit'],rule:'Use short database transactions. Model and API calls happen outside them.',concepts:['agent','policy','pubsub','lifecycle']},
  {id:'llm',no:'06',title:'LLM API',sub:'Propose calls and responses',x:35,y:400,type:'external',tech:'Provider adapter · structured output',description:'The model proposes a tool request or customer answer. The worker validates the proposal before execution and records the observed result.',does:['Select permitted tool schemas','Use observed facts in the response','Return structured requests and usage'],rule:'Model output cannot grant permission or approve a refund.',concepts:['agent','policy','evaluation']},
  {id:'mock',no:'07',title:'Mock Enterprise APIs',sub:'Orders, payments, refunds',x:705,y:400,type:'service',tech:'Synthetic records · idempotent mock writes',description:'The worker calls mock order and payment APIs after its checks pass. These APIs return scoped data and apply one effect per logical refund key.',does:['Return order and payment evidence','Record mock refunds by operation key','Simulate timeouts and uncertain results'],rule:'A timeout after a write means the outcome is uncertain. Reuse the existing action key.',concepts:['idempotency','delivery','evaluation']}
];
let selectedComponent = 'gateway';
const colors = {service:['#f7f9f3','#d4ddce'], storage:['#eaf3eb','#b4cbb8'],external:['#f2eff7','#d9cfe4']};
// Vertical execution path, with horizontal calls to storage and external APIs.
function renderMap() {
  const node = (id,x,y,sub,note='') => {
    const c = components.find(item=>item.id===id);
    return `<g class="node ${selectedComponent===id?'selected':''}" role="button" tabindex="0" aria-label="${escapeHTML(c.title)}: ${escapeHTML(sub)}. ${escapeHTML(note)}" aria-pressed="${selectedComponent===id}" data-component="${id}" transform="translate(${x} ${y})"><rect width="260" height="100" rx="10" fill="${colors[c.type][0]}" stroke="${colors[c.type][1]}"/><text x="15" y="24" class="node-title">${escapeHTML(c.title)}</text><text x="15" y="50" class="node-sub">${escapeHTML(sub)}</text><text x="15" y="76" class="node-sub">${escapeHTML(note)}</text>${selectedComponent===id?'<circle class="selected-indicator" cx="244" cy="16" r="3.5"/>':''}</g>`;
  };
  const arrow = (path,label,x,y,{live=false,both=false}={}) => `<path class="edge ${live?'status-edge':''}" d="${path}" marker-end="url(#${live?'arrow-status':'arrow'})" ${both?`marker-start="url(#${live?'arrow-status':'arrow'})"`:''}/><text class="edge-label" x="${x}" y="${y}" text-anchor="middle">${escapeHTML(label)}</text>`;
  const stage = (y,height,title) => `<rect class="flow-stage" x="5" y="${y}" width="990" height="${height}" rx="12"/><text class="stage-title" x="25" y="${y+26}">${title}</text>`;
  $('#architecture-map').innerHTML = `<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7" fill="#aeb9ae"/></marker><marker id="arrow-status" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7" fill="#376b56"/></marker></defs>
    ${stage(5,465,'A / ACCEPT THE REQUEST')}
    ${stage(490,320,'B / RUN THE WORK · CHECKS STAY IN THE WORKER')}
    ${stage(830,495,'C / STREAM EACH SAVED STEP')}
    ${arrow('M500 155 V215','1 · signed webhook',590,187)}
    ${arrow('M370 250 H280','2 · save + commit',210,202)}
    ${arrow('M500 315 V365','3 · enqueue run ID',590,345)}
    ${arrow('M500 465 V570','4 · consume job',585,548)}
    ${arrow('M630 595 H675 V570 H720','5a · model I/O',820,505,{both:true})}
    ${arrow('M630 645 H675 V720 H720','5b · checked tools',688,775,{both:true})}
    ${arrow('M370 630 H280','6 · commit step',215,564)}
    ${arrow('M500 670 V880','7 · publish after commit',585,790,{live:true})}
    ${arrow('M500 980 V1040','8 · progress notice',590,1015,{live:true})}
    ${arrow('M370 1090 H280','9 · read saved events',210,1025,{live:true,both:true})}
    ${arrow('M500 1140 V1200','10 · SSE events',585,1176,{live:true})}
    ${node('customer',370,55,'Customer message','Simulator in the local demo')}
    ${node('gateway',370,215,'Verify and accept the webhook','Commit before queue submission')}
    ${node('database',20,215,'Save input + pending run','One database transaction')}
    ${node('queue',370,365,'Role 1: RQ job queue','Holds the saved run ID')}
    ${node('agent',370,570,'Load run · check access + policy','Repeat: execute → save → publish')}
    ${node('database',20,580,'Save state + run_events','At start, progress, and outcome')}
    ${node('llm',720,520,'Propose calls and responses','Planned · fake agent today')}
    ${node('mock',720,670,'Return checked order data','Refunds remain planned')}
    ${node('queue',370,880,'Role 2: Pub/Sub notices','Same Redis · transient notices')}
    ${node('gateway',370,1040,'Subscribe → read → stream','Subscribe before replay')}
    ${node('database',20,1040,'Read the saved event history','On a notice or reconnect')}
    ${node('dashboard',370,1200,'Display the saved timeline','Planned operator interface')}
    <text class="flow-note" x="25" y="355">If step 3 fails after commit,</text><text class="flow-note" x="25" y="376">the saved run needs manual retry.</text>
    <text class="flow-note" x="25" y="730">The worker also reads saved input</text><text class="flow-note" x="25" y="751">from PostgreSQL before execution.</text>
    <text class="flow-note" x="720" y="910">Publish a notice after each commit.</text><text class="flow-note" x="720" y="932">The notice does not contain history.</text>
    <text class="flow-note" x="720" y="1070">Replay recovers missed notices.</text><text class="flow-note" x="720" y="1092">No routine database polling.</text>`;
  const c = components.find(c=>c.id===selectedComponent);
  $('#inspector').innerHTML = `<div class="inspector-top"><span class="component-number">COMPONENT ${c.no} / ${components.length}</span><span class="tag">${c.type==='storage'?'DURABLE STATE':c.type==='external'?'INTERFACE':'APPLICATION'}</span></div><h2>${c.title}</h2><div class="component-tech">${c.tech}</div><div><p>${c.description}</p><h3>WHAT IT DOES</h3><ul class="responsibilities">${c.does.map(s=>`<li>${s}</li>`).join('')}</ul></div><div><h3>CONNECTED CONCEPTS</h3><div class="concept-chips">${c.concepts.map(chip).join('')}</div><div class="component-rule">${c.rule}</div><h3>GO ONE LEVEL DEEPER</h3><a class="text-link" href="${obsidianURI('System Design')}">Open the design in Obsidian ↗</a></div>`;
}

function step(node,title,description,event,payload,learn,extra={}){return {node,title,description,event,payload,learn,...extra};}
const common = () => [
  step('customer','A message arrives.','The simulator sends a signed customer message with a stable event ID. All names, orders, and amounts in this walkthrough are synthetic.','support.message_received',{event_id:'evt_001',conversation_id:'conv_42',customer_id:'customer_17'},['events','webhooks']),
  step('gateway','Accept it durably.','The gateway verifies the signature and derives the tenant from trusted credentials. One PostgreSQL transaction saves the event, message, pending run, and run.received history event. Queue submission follows this commit.','run.received',{status:'pending',transaction:'event + message + pending run',tenant:'verified integration context'},['webhooks','lifecycle']),
  step('gateway','Enqueue the saved run.','FastAPI submits run_42 to RQ after the database commit. It returns 202 when submission succeeds. A crash before submission leaves a pending run that needs a sender or operator retry.','queue.submitted',{queue:'support',job:{run_id:'run_42'},http_status:202,status:'pending until a worker starts'},['queue','lifecycle']),
  step('agent','A worker takes ownership.','The RQ entry point starts the async runtime. It checks ticket ownership and loads the saved run. It commits running status and run.started before asking the model what to do.','run.started',{run_id:'run_42',status:'running',attempt_id:'attempt_1',max_model_turns:8},['queue','leases','agent']),
  step('queue','Publish the committed step.','The worker has saved run.started in PostgreSQL. It publishes the run ID and sequence to Redis Pub/Sub. FastAPI receives the notice, reads missing saved events, and sends them through SSE. No status polling is used.','stream.notice_published',{channel:'support:dev:tenant:tenant_17:run-events',run_id:'run_42',sequence:2,order:'commit → publish → read → SSE'},['pubsub','sse','lifecycle'])
];
const scenarios = {
  order:{title:'Where is my order?',subtitle:'Read-only resolution · synthetic order ORD-1001',steps:[...common(),
    step('llm','Ask for evidence.','The model proposes get_order. It does not invent the shipment status or choose a tenant. The runtime routes the request through the worker.','tool.requested',{tool:'get_order',arguments:{order_id:'ORD-1001'}},['agent','policy']),
    step('agent','Check ownership, then read.','The worker checks that the verified customer owns the order. The mock API returns the shipment status. The runtime saves a redacted result.','tool.completed',{order_id:'ORD-1001',shipment:'in_transit',evidence:'mock orders API'},['isolation','policy']),
    step('database','Commit the answer and delivery intent.','Using the observed shipment result, the agent produces a response. The database commits the response, completed state, run.completed event, and a pending delivery record together.','run.completed',{outcome:'answered',response:'Your order is in transit.',delivery:'pending'},['lifecycle','observability']),
    step('dashboard','Deliver the response. Keep the trail.','A delivery job sends the response to the simulator. After each commit, a Redis Pub/Sub notice signals FastAPI to stream saved events through SSE. The customer and operator use different interfaces.','response.delivered',{destination:'simulator',delivery:'confirmed',operator_stream:'Redis Pub/Sub → FastAPI SSE'},['sse','observability'])]},
  refund:{title:'A refund with approval',subtitle:'Controlled write · synthetic £25.00 refund',steps:[...common(),
    step('agent','Look up facts and check policy.','The model requests order and payment information. The worker checks ownership and applies the current refund policy in code. In this illustrative scenario the £25 refund is eligible.','refund.eligible',{order_id:'ORD-1001',amount_minor:2500,currency:'GBP',policy:'demo-policy-v1'},['agent','policy']),
    step('agent','Pause for a person.','The run checkpoints an exact proposed action, enters waiting_approval, and releases the worker. An approval is bound to this payment, amount, currency, and arguments hash.','approval.requested',{action_id:'refund_42',amount_minor:2500,currency:'GBP',status:'waiting_approval'},['approval','recovery'],{approval:true}),
    step('agent','Resume, then recheck.','FastAPI saves the authorized decision, then submits the saved run ID to RQ. A worker resumes the checkpoint and rechecks current eligibility, approval expiry, and the action hash before issuing a write.','approval.decided',{decision:'approved',action_id:'refund_42',continuation:'queued and resumed'},['approval','leases']),
    step('mock','Execute one logical refund.','The mock payments API enforces refund_42 as a stable idempotency key. The runtime records the provider’s result before creating the customer response.','tool.completed',{tool:'execute_refund',idempotency_key:'refund_42',provider_refund:'mock_ref_001',effect_count:1},['idempotency','policy']),
    step('dashboard','Close with a recorded outcome.','The response, completed status, history event, and pending delivery are committed. A delivery job confirms the reply to the simulator; the operator sees the approval and effect in the same durable timeline.','run.completed',{outcome:'refunded',amount_minor:2500,currency:'GBP',effect_count:1},['observability','evaluation'])]},
  duplicate:{title:'The same refund, twice',subtitle:'Ambiguous write recovery · one logical action',steps:[...common(),
    step('agent','An exact action is already approved.','This scenario begins with an authorized synthetic £25 refund. Policy and approval bind the action to refund_42; retries must preserve that identity.','approval.verified',{action_id:'refund_42',approval:'valid',amount_minor:2500,currency:'GBP'},['approval','idempotency']),
    step('mock','The refund succeeds. The reply is lost.','The mock payments API records the refund, but the worker loses the response. A timeout does not tell us whether the money-moving effect happened.','tool.outcome_unknown',{action_id:'refund_42',provider_effect:'committed',worker_observation:'timeout'},['delivery','idempotency']),
    step('agent','Recover the same action.','After an expired lease, recovery loads the durable action record. It queries the provider by the existing operation key rather than inventing a new refund identity.','run.recovering',{action_id:'refund_42',fencing_token:8,operation:'lookup by idempotency key'},['recovery','leases']),
    step('mock','Return the original result.','The provider finds refund_42 and returns mock_ref_001. A matching retry under the same key would also return that result. Changed arguments under the same key are rejected.','tool.reconciled',{action_id:'refund_42',provider_refund:'mock_ref_001',effect_count:1},['idempotency','delivery']),
    step('database','Repeated attempts. One effect.','The reconciled result is committed and the run can complete. The guarantee comes from durable action identity plus provider enforcement, rather than from queue delivery happening exactly once.','run.completed',{attempts:2,logical_refunds:1,refund_effects:1,outcome:'reconciled'},['idempotency','evaluation'])]}
};
let currentScenario='order',currentStep=0,playTimer=null,rejected=false;
function pause(){clearInterval(playTimer);playTimer=null;$('#play').textContent='Play journey';}
function renderJourney(){
  const scenario=scenarios[currentScenario],s=scenario.steps[currentStep],component=components.find(c=>c.id===s.node);
  $('#scenario-title').textContent=scenario.title;
  $('#scenario-subtitle').textContent=scenario.subtitle;
  $$('.scenario-picker button').forEach(b=>{b.classList.toggle('selected',b.dataset.scenario===currentScenario);b.setAttribute('aria-pressed',b.dataset.scenario===currentScenario);});
  $('#journey-progress').style.width=`${(currentStep+1)/scenario.steps.length*100}%`;
  $('#journey-content').innerHTML = rejected ? `<div class="step-count">HUMAN DECISION / REJECTED</div><div class="step-node">Operator approval</div><h3>Escalate without a refund.</h3><p class="step-description">The operator rejected the proposal. The run records a valid business outcome and routes the ticket for human handling. No refund tool executes.</p><pre class="event-code">${escapeHTML(JSON.stringify({event:'run.escalated',reason:'approval_rejected',refund_effects:0},null,2))}</pre><div class="step-learning">Understand why ${chip('approval')}${chip('policy')}</div>` : `<div class="step-count">STEP ${String(currentStep+1).padStart(2,'0')} / ${String(scenario.steps.length).padStart(2,'0')}</div><div class="step-node">${component.title}</div><h3>${s.title}</h3><p class="step-description">${s.description}</p><pre class="event-code">${escapeHTML(JSON.stringify(s.payload,null,2))}</pre><div class="step-learning">THE IDEA BEHIND THIS STEP ${s.learn.map(chip).join('')}</div>${s.approval?'<div class="approval-box"><strong>Waiting for operator approval</strong><p>Simulation only · £25.00 GBP · ORD-1001 · action refund_42</p><div class="approval-actions"><button class="button primary" id="approve">Approve & continue →</button><button class="button secondary" id="reject">Reject & escalate</button></div></div>':''}`;
  $('#next').disabled=Boolean(s.approval)||currentStep===scenario.steps.length-1||rejected;
  $('#next').textContent = rejected?'Escalated':currentStep===scenario.steps.length-1?'Journey complete ✓':s.approval?'Awaiting approval':'Next step →';
  $('#play').disabled=Boolean(s.approval)||currentStep===scenario.steps.length-1||rejected;
  const trace=scenario.steps.slice(0,currentStep+1);
  $('#trace-list').innerHTML=trace.map((item,i)=>`<li class="${i===currentStep&&!rejected?'current':''}"><small>${String(i+1).padStart(2,'0')} / ${components.find(c=>c.id===item.node).title}</small><strong>${item.event}</strong><span>${item.title}</span></li>`).join('')+(rejected?'<li class="current"><small>HUMAN DECISION</small><strong>run.escalated</strong><span>Rejected; no refund executed.</span></li>':'');
  if(s.approval||rejected||currentStep===scenario.steps.length-1)pause();
}
function advance(){const steps=scenarios[currentScenario].steps;if(rejected||steps[currentStep].approval||currentStep>=steps.length-1)return;currentStep++;renderJourney();}
$('#next').addEventListener('click',advance);
$('#restart').addEventListener('click',()=>{pause();currentStep=0;rejected=false;renderJourney();});
$('#play').addEventListener('click',()=>{if(playTimer){pause();return;}$('#play').textContent='Pause';playTimer=setInterval(advance,1800);});
$$('[data-scenario]').forEach(b=>b.addEventListener('click',()=>{pause();currentScenario=b.dataset.scenario;currentStep=0;rejected=false;renderJourney();}));

let activeCategory='All',selectedConcept='pubsub';
let reviewed=new Set();
try{const saved=JSON.parse(localStorage.getItem('support-engine-reviewed')||'[]');if(Array.isArray(saved))reviewed=new Set(saved.filter(id=>conceptById[id]));}catch{}
function renderLibrary(){
  const query=$('#concept-search').value.trim().toLowerCase();
  const filtered=concepts.filter(c=>(activeCategory==='All'||c.category===activeCategory)&&`${c.title} ${c.summary} ${c.explanation} ${c.example} ${c.question}`.toLowerCase().includes(query));
  $('#category-filters').innerHTML=['All',...new Set(concepts.map(c=>c.category))].map(category=>`<button data-category="${category}" class="${activeCategory===category?'selected':''}" aria-pressed="${activeCategory===category}">${category}</button>`).join('');
  $('#result-count').textContent=`${filtered.length} CONCEPT${filtered.length===1?'':'S'}${query?' MATCHING YOUR SEARCH':''}`;
  $('#review-count').textContent=reviewed.size;
  $('#concept-list').innerHTML=filtered.length?filtered.map(c=>`<button class="concept-item ${selectedConcept===c.id?'selected':''}" data-note="${c.id}" aria-pressed="${selectedConcept===c.id}"><small>${c.category}</small>${reviewed.has(c.id)?'<span class="reviewed" aria-label="Reviewed">✓</span>':''}<strong>${c.title}</strong><span>${c.summary}</span></button>`).join(''):'<p class="empty-state">No matching concepts. Try a broader search or choose another category.</p>';
  if(filtered.length&&!filtered.some(c=>c.id===selectedConcept))selectedConcept=filtered[0].id;
  if(!filtered.length){$('#note-preview').innerHTML='<div class="eyebrow">NO MATCHES</div><h2>Keep exploring.</h2><p>Try “refund”, “recovery”, or “queue”, or clear the filters to return to the full library.</p><button class="button secondary" id="clear-search">Clear search and filters</button>';return;}
  const c=conceptById[selectedConcept];
  $$('#concept-list [data-note]').forEach(b=>{b.classList.toggle('selected',b.dataset.note===selectedConcept);b.setAttribute('aria-pressed',b.dataset.note===selectedConcept);});
  $('#note-preview').innerHTML=`<div class="eyebrow">${c.category.toUpperCase()} / CONCEPT NOTE</div><h2>${c.title}</h2><div class="note-summary">${c.summary}</div><h3>Understand it</h3><p>${c.explanation}</p><h3>In this project</h3><p>${c.example}</p><h3>A common mistake</h3><p>${c.pitfall}</p><div class="interview"><h3>Interview practice</h3><strong>${c.question}</strong><p>${c.answer}</p></div><h3>Connected ideas</h3><div class="concept-chips">${c.related.map(chip).join('')}</div><div class="note-actions"><a class="button primary" href="${obsidianURI(c.title,true)}">Open in Obsidian ↗</a><button class="button secondary" id="review-note" aria-pressed="${reviewed.has(c.id)}">${reviewed.has(c.id)?'✓ Reviewed in browser':'Mark as reviewed'}</button></div><a class="source-link" href="${c.source}" target="_blank" rel="noopener noreferrer">Further reading: ${c.sourceLabel} ↗</a>`;
}
$('#concept-search').addEventListener('input',renderLibrary);

const milestones=[
  ['Saved job lifecycle','Save the event. Execute its job. Record the outcome.',['Signed webhook and pending run saved in PostgreSQL','Direct submission of the saved run ID to RQ','Worker saves start, steps, and final state'],['A repeated webhook creates one logical run.','An operator can retry a failed enqueue using its saved run ID.'],['events','lifecycle','queue']],
  ['A tool-using agent','Give the runtime evidence, tools, and stopping conditions.',['Provider adapter and deterministic fake model','Bounded async tool-use runtime','Customer-scoped order and payment tools'],['Order questions resolve using observed facts.','Unknown tools and execution budget violations are handled.'],['agent','policy','evaluation']],
  ['Controlled refunds','Make a consequential action resumable and auditable.',['Versioned eligibility rules','Exact-action approval and continuation','Idempotent mock payment writes'],['Duplicate attempts create one refund.','A crash after an external write can be reconciled.'],['approval','idempotency','recovery']],
  ['The operator dashboard','Make progress and decisions visible.',['Redis Pub/Sub subscription and local browser fan-out','Subscribe-before-replay with SSE sequence cursors','Approval UI with server-side role enforcement'],['A disconnected client catches up without missing persisted events.','Unauthorized subscriptions and approvals are denied.'],['pubsub','sse','isolation']],
  ['Reliability and evaluation','Prove behavior under mistakes, faults, and overload.',['Selected automatic recovery method and fault scenarios','Versioned 30–50-scenario evaluation dataset','Queue-age, retry, and resource metrics'],['Worker and queue recovery tests pass.','Publish measured quality, latency, cost, and limitations.'],['leases','backpressure','evaluation']],
  ['Portfolio release','Make the project reproducible and explain its decisions.',['Docker Compose, seed data, and documented demo commands','Architecture decisions and benchmark report','Recorded success, denial, and crash-recovery walkthroughs'],['A reviewer can run the demo using a deterministic fake provider.','The README links to results, tradeoffs, and known limitations.'],['observability','evaluation','events']]
];
$('#milestones').innerHTML=milestones.map(([title,description,deliverables,checks,learn],i)=>`<details class="milestone" ${i===0?'open':''}><summary><span class="milestone-number">${String(i+1).padStart(2,'0')}</span><div><h2>${title}</h2><p>${description}</p></div><span class="tag">PLANNED</span><span class="expand-icon">+</span></summary><div class="milestone-content"><h3>WHAT YOU BUILD</h3><ul>${deliverables.map(t=>`<li>${t}</li>`).join('')}</ul><h3>DONE WHEN</h3><ul>${checks.map(t=>`<li>${t}</li>`).join('')}</ul><div class="concept-chips">${learn.map(chip).join('')}</div></div></details>`).join('');

const pageNames={architecture:'System map',walkthrough:'Request walkthrough',knowledge:'Knowledge library',roadmap:'Build roadmap'};
function navigate(){
  let page=location.hash.slice(1)||'architecture';
  if(!pageNames[page])page='architecture';
  $$('.page').forEach(p=>{p.hidden=p.id!==`page-${page}`;});
  $$('nav [data-page]').forEach(a=>{if(a.dataset.page===page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#breadcrumb').textContent=pageNames[page];
  document.title=`${pageNames[page]} · Support Engine`;
  if(page!=='walkthrough')pause();
  window.scrollTo({top:0,behavior:'instant'});
}
function openConcept(id){if(!conceptById[id])return;selectedConcept=id;activeCategory='All';$('#concept-search').value='';renderLibrary();if(location.hash!=='#knowledge')location.hash='knowledge';else $('#note-preview').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});}
document.addEventListener('click',event=>{
  const component=event.target.closest('[data-component]');if(component){selectedComponent=component.dataset.component;renderMap();const active=$(`[data-component="${selectedComponent}"]`);if(event.detail===0)active?.focus();return;}
  const concept=event.target.closest('[data-concept]');if(concept){openConcept(concept.dataset.concept);return;}
  const note=event.target.closest('[data-note]');if(note){selectedConcept=note.dataset.note;renderLibrary();return;}
  const category=event.target.closest('[data-category]');if(category){activeCategory=category.dataset.category;renderLibrary();return;}
  if(event.target.closest('#clear-search')){activeCategory='All';$('#concept-search').value='';renderLibrary();return;}
  if(event.target.closest('#review-note')){reviewed.has(selectedConcept)?reviewed.delete(selectedConcept):reviewed.add(selectedConcept);try{localStorage.setItem('support-engine-reviewed',JSON.stringify([...reviewed]));toast('Review mark saved in this browser.');}catch{toast('Review mark kept for this session; browser storage is unavailable.');}renderLibrary();return;}
  if(event.target.closest('#approve')){if(currentScenario==='refund'&&scenarios.refund.steps[currentStep].approval){currentStep++;renderJourney();}return;}
  if(event.target.closest('#reject')){rejected=true;pause();renderJourney();return;}
});
$('#architecture-map').addEventListener('keydown',event=>{const node=event.target.closest('[data-component]');if(node&&(event.key==='Enter'||event.key===' ')){event.preventDefault();node.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
$$('[data-obsidian]').forEach(a=>{a.href=obsidianURI(a.dataset.obsidian);});
$$('[data-concept-count]').forEach(el=>{el.textContent=concepts.length;});
window.addEventListener('hashchange',navigate);
renderMap();renderJourney();renderLibrary();navigate();
