---- MODULE ServerFederation_TTrace_1767190099 ----
EXTENDS ServerFederation_TEConstants, ServerFederation, Sequences, TLCExt, Toolbox, Naturals, TLC

_expression ==
    LET ServerFederation_TEExpression == INSTANCE ServerFederation_TEExpression
    IN ServerFederation_TEExpression!expression
----

_trace ==
    LET ServerFederation_TETrace == INSTANCE ServerFederation_TETrace
    IN ServerFederation_TETrace!trace
----

_inv ==
    ~(
        TLCGet("level") = Len(_TETrace)
        /\
        primaryNode = (contributor1)
        /\
        time = (0)
        /\
        nodeStatus = ((hetzner :> "DEGRADED" @@ backup :> "HEALTHY" @@ contributor1 :> "UNKNOWN"))
        /\
        failureCount = ((hetzner :> 1 @@ backup :> 0 @@ contributor1 :> 0))
    )
----

_init ==
    /\ time = _TETrace[1].time
    /\ nodeStatus = _TETrace[1].nodeStatus
    /\ primaryNode = _TETrace[1].primaryNode
    /\ failureCount = _TETrace[1].failureCount
----

_next ==
    /\ \E i,j \in DOMAIN _TETrace:
        /\ \/ /\ j = i + 1
              /\ i = TLCGet("level")
        /\ time  = _TETrace[i].time
        /\ time' = _TETrace[j].time
        /\ nodeStatus  = _TETrace[i].nodeStatus
        /\ nodeStatus' = _TETrace[j].nodeStatus
        /\ primaryNode  = _TETrace[i].primaryNode
        /\ primaryNode' = _TETrace[j].primaryNode
        /\ failureCount  = _TETrace[i].failureCount
        /\ failureCount' = _TETrace[j].failureCount

\* Uncomment the ASSUME below to write the states of the error trace
\* to the given file in Json format. Note that you can pass any tuple
\* to `JsonSerialize`. For example, a sub-sequence of _TETrace.
    \* ASSUME
    \*     LET J == INSTANCE Json
    \*         IN J!JsonSerialize("ServerFederation_TTrace_1767190099.json", _TETrace)

=============================================================================

 Note that you can extract this module `ServerFederation_TEExpression`
  to a dedicated file to reuse `expression` (the module in the 
  dedicated `ServerFederation_TEExpression.tla` file takes precedence 
  over the module `ServerFederation_TEExpression` below).

---- MODULE ServerFederation_TEExpression ----
EXTENDS ServerFederation_TEConstants, ServerFederation, Sequences, TLCExt, Toolbox, Naturals, TLC

expression == 
    [
        \* To hide variables of the `ServerFederation` spec from the error trace,
        \* remove the variables below.  The trace will be written in the order
        \* of the fields of this record.
        time |-> time
        ,nodeStatus |-> nodeStatus
        ,primaryNode |-> primaryNode
        ,failureCount |-> failureCount
        
        \* Put additional constant-, state-, and action-level expressions here:
        \* ,_stateNumber |-> _TEPosition
        \* ,_timeUnchanged |-> time = time'
        
        \* Format the `time` variable as Json value.
        \* ,_timeJson |->
        \*     LET J == INSTANCE Json
        \*     IN J!ToJson(time)
        
        \* Lastly, you may build expressions over arbitrary sets of states by
        \* leveraging the _TETrace operator.  For example, this is how to
        \* count the number of times a spec variable changed up to the current
        \* state in the trace.
        \* ,_timeModCount |->
        \*     LET F[s \in DOMAIN _TETrace] ==
        \*         IF s = 1 THEN 0
        \*         ELSE IF _TETrace[s].time # _TETrace[s-1].time
        \*             THEN 1 + F[s-1] ELSE F[s-1]
        \*     IN F[_TEPosition - 1]
    ]

=============================================================================



Parsing and semantic processing can take forever if the trace below is long.
 In this case, it is advised to uncomment the module below to deserialize the
 trace from a generated binary file.

\*
\*---- MODULE ServerFederation_TETrace ----
\*EXTENDS ServerFederation_TEConstants, ServerFederation, IOUtils, TLC
\*
\*trace == IODeserialize("ServerFederation_TTrace_1767190099.bin", TRUE)
\*
\*=============================================================================
\*

---- MODULE ServerFederation_TETrace ----
EXTENDS ServerFederation_TEConstants, ServerFederation, TLC

trace == 
    <<
    ([primaryNode |-> hetzner,time |-> 0,nodeStatus |-> (hetzner :> "HEALTHY" @@ backup :> "UNKNOWN" @@ contributor1 :> "UNKNOWN"),failureCount |-> (hetzner :> 0 @@ backup :> 0 @@ contributor1 :> 0)]),
    ([primaryNode |-> hetzner,time |-> 0,nodeStatus |-> (hetzner :> "HEALTHY" @@ backup :> "HEALTHY" @@ contributor1 :> "UNKNOWN"),failureCount |-> (hetzner :> 0 @@ backup :> 0 @@ contributor1 :> 0)]),
    ([primaryNode |-> contributor1,time |-> 0,nodeStatus |-> (hetzner :> "DEGRADED" @@ backup :> "HEALTHY" @@ contributor1 :> "UNKNOWN"),failureCount |-> (hetzner :> 1 @@ backup :> 0 @@ contributor1 :> 0)])
    >>
----


=============================================================================

---- MODULE ServerFederation_TEConstants ----
EXTENDS ServerFederation

CONSTANTS hetzner, backup, contributor1

=============================================================================

---- CONFIG ServerFederation_TTrace_1767190099 ----
CONSTANTS
    Nodes = { hetzner , backup , contributor1 }
    HUB = hetzner
    MaxFailures = 3
    hetzner = hetzner
    backup = backup
    contributor1 = contributor1

INVARIANT
    _inv

CHECK_DEADLOCK
    \* CHECK_DEADLOCK off because of PROPERTY or INVARIANT above.
    FALSE

INIT
    _init

NEXT
    _next

CONSTANT
    _TETrace <- _trace

ALIAS
    _expression
=============================================================================
\* Generated on Wed Dec 31 15:08:20 CET 2025