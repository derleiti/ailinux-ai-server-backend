---- MODULE LoadBalancer_TTrace_1767191105 ----
EXTENDS Sequences, TLCExt, LoadBalancer_TEConstants, Toolbox, LoadBalancer, Naturals, TLC

_expression ==
    LET LoadBalancer_TEExpression == INSTANCE LoadBalancer_TEExpression
    IN LoadBalancer_TEExpression!expression
----

_trace ==
    LET LoadBalancer_TETrace == INSTANCE LoadBalancer_TETrace
    IN LoadBalancer_TETrace!trace
----

_inv ==
    ~(
        TLCGet("level") = Len(_TETrace)
        /\
        totalRouted = (4)
        /\
        routedTo = (n1)
        /\
        nodeLoad = ((n1 :> 2 @@ n2 :> 0 @@ n3 :> 1))
        /\
        requestQueue = (<<>>)
        /\
        nodeStatus = ((n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy"))
    )
----

_init ==
    /\ requestQueue = _TETrace[1].requestQueue
    /\ nodeLoad = _TETrace[1].nodeLoad
    /\ totalRouted = _TETrace[1].totalRouted
    /\ nodeStatus = _TETrace[1].nodeStatus
    /\ routedTo = _TETrace[1].routedTo
----

_next ==
    /\ \E i,j \in DOMAIN _TETrace:
        /\ \/ /\ j = i + 1
              /\ i = TLCGet("level")
        /\ requestQueue  = _TETrace[i].requestQueue
        /\ requestQueue' = _TETrace[j].requestQueue
        /\ nodeLoad  = _TETrace[i].nodeLoad
        /\ nodeLoad' = _TETrace[j].nodeLoad
        /\ totalRouted  = _TETrace[i].totalRouted
        /\ totalRouted' = _TETrace[j].totalRouted
        /\ nodeStatus  = _TETrace[i].nodeStatus
        /\ nodeStatus' = _TETrace[j].nodeStatus
        /\ routedTo  = _TETrace[i].routedTo
        /\ routedTo' = _TETrace[j].routedTo

\* Uncomment the ASSUME below to write the states of the error trace
\* to the given file in Json format. Note that you can pass any tuple
\* to `JsonSerialize`. For example, a sub-sequence of _TETrace.
    \* ASSUME
    \*     LET J == INSTANCE Json
    \*         IN J!JsonSerialize("LoadBalancer_TTrace_1767191105.json", _TETrace)

=============================================================================

 Note that you can extract this module `LoadBalancer_TEExpression`
  to a dedicated file to reuse `expression` (the module in the 
  dedicated `LoadBalancer_TEExpression.tla` file takes precedence 
  over the module `LoadBalancer_TEExpression` below).

---- MODULE LoadBalancer_TEExpression ----
EXTENDS Sequences, TLCExt, LoadBalancer_TEConstants, Toolbox, LoadBalancer, Naturals, TLC

expression == 
    [
        \* To hide variables of the `LoadBalancer` spec from the error trace,
        \* remove the variables below.  The trace will be written in the order
        \* of the fields of this record.
        requestQueue |-> requestQueue
        ,nodeLoad |-> nodeLoad
        ,totalRouted |-> totalRouted
        ,nodeStatus |-> nodeStatus
        ,routedTo |-> routedTo
        
        \* Put additional constant-, state-, and action-level expressions here:
        \* ,_stateNumber |-> _TEPosition
        \* ,_requestQueueUnchanged |-> requestQueue = requestQueue'
        
        \* Format the `requestQueue` variable as Json value.
        \* ,_requestQueueJson |->
        \*     LET J == INSTANCE Json
        \*     IN J!ToJson(requestQueue)
        
        \* Lastly, you may build expressions over arbitrary sets of states by
        \* leveraging the _TETrace operator.  For example, this is how to
        \* count the number of times a spec variable changed up to the current
        \* state in the trace.
        \* ,_requestQueueModCount |->
        \*     LET F[s \in DOMAIN _TETrace] ==
        \*         IF s = 1 THEN 0
        \*         ELSE IF _TETrace[s].requestQueue # _TETrace[s-1].requestQueue
        \*             THEN 1 + F[s-1] ELSE F[s-1]
        \*     IN F[_TEPosition - 1]
    ]

=============================================================================



Parsing and semantic processing can take forever if the trace below is long.
 In this case, it is advised to uncomment the module below to deserialize the
 trace from a generated binary file.

\*
\*---- MODULE LoadBalancer_TETrace ----
\*EXTENDS IOUtils, LoadBalancer_TEConstants, LoadBalancer, TLC
\*
\*trace == IODeserialize("LoadBalancer_TTrace_1767191105.bin", TRUE)
\*
\*=============================================================================
\*

---- MODULE LoadBalancer_TETrace ----
EXTENDS LoadBalancer_TEConstants, LoadBalancer, TLC

trace == 
    <<
    ([totalRouted |-> 0,routedTo |-> n1,nodeLoad |-> (n1 :> 0 @@ n2 :> 0 @@ n3 :> 0),requestQueue |-> <<>>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 0,routedTo |-> n1,nodeLoad |-> (n1 :> 0 @@ n2 :> 0 @@ n3 :> 0),requestQueue |-> <<"request">>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 1,routedTo |-> n1,nodeLoad |-> (n1 :> 1 @@ n2 :> 0 @@ n3 :> 0),requestQueue |-> <<>>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 1,routedTo |-> n1,nodeLoad |-> (n1 :> 1 @@ n2 :> 0 @@ n3 :> 0),requestQueue |-> <<"request">>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 1,routedTo |-> n1,nodeLoad |-> (n1 :> 1 @@ n2 :> 0 @@ n3 :> 0),requestQueue |-> <<"request", "request">>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 1,routedTo |-> n1,nodeLoad |-> (n1 :> 1 @@ n2 :> 0 @@ n3 :> 0),requestQueue |-> <<"request", "request", "request">>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 2,routedTo |-> n2,nodeLoad |-> (n1 :> 1 @@ n2 :> 1 @@ n3 :> 0),requestQueue |-> <<"request", "request">>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 3,routedTo |-> n3,nodeLoad |-> (n1 :> 1 @@ n2 :> 1 @@ n3 :> 1),requestQueue |-> <<"request">>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 4,routedTo |-> n1,nodeLoad |-> (n1 :> 2 @@ n2 :> 1 @@ n3 :> 1),requestQueue |-> <<>>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")]),
    ([totalRouted |-> 4,routedTo |-> n1,nodeLoad |-> (n1 :> 2 @@ n2 :> 0 @@ n3 :> 1),requestQueue |-> <<>>,nodeStatus |-> (n1 :> "healthy" @@ n2 :> "healthy" @@ n3 :> "healthy")])
    >>
----


=============================================================================

---- MODULE LoadBalancer_TEConstants ----
EXTENDS LoadBalancer

CONSTANTS n1, n2, n3

=============================================================================

---- CONFIG LoadBalancer_TTrace_1767191105 ----
CONSTANTS
    Nodes = { n1 , n2 , n3 }
    MaxLoad = 3
    MaxQueueSize = 5
    n1 = n1
    n2 = n2
    n3 = n3

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
\* Generated on Wed Dec 31 15:25:05 CET 2025