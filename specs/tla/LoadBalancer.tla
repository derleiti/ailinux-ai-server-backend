---------------------------- MODULE LoadBalancer ----------------------------
EXTENDS Naturals, FiniteSets, Sequences

CONSTANTS Nodes, MaxLoad, MaxQueueSize

VARIABLES nodeLoad, nodeStatus, requestQueue, routedTo

vars == <<nodeLoad, nodeStatus, requestQueue, routedTo>>

Status == {"healthy", "degraded", "offline"}

TypeInvariant ==
    /\ nodeLoad \in [Nodes -> 0..MaxLoad]
    /\ nodeStatus \in [Nodes -> Status]
    /\ Len(requestQueue) <= MaxQueueSize
    /\ routedTo \in Nodes

AvailableNodes ==
    {x \in Nodes : nodeStatus[x] \in {"healthy", "degraded"} /\ nodeLoad[x] < MaxLoad}

LeastLoadedNode ==
    IF AvailableNodes = {} THEN CHOOSE x \in Nodes : TRUE
    ELSE CHOOSE x \in AvailableNodes : \A y \in AvailableNodes : nodeLoad[x] <= nodeLoad[y]

HasAvailableNode == AvailableNodes /= {}

Init ==
    /\ nodeLoad = [x \in Nodes |-> 0]
    /\ nodeStatus = [x \in Nodes |-> "healthy"]
    /\ requestQueue = <<>>
    /\ routedTo = CHOOSE x \in Nodes : TRUE

RequestArrives ==
    /\ Len(requestQueue) < MaxQueueSize
    /\ requestQueue' = Append(requestQueue, "r")
    /\ UNCHANGED <<nodeLoad, nodeStatus, routedTo>>

RouteRequest ==
    /\ Len(requestQueue) > 0
    /\ HasAvailableNode
    /\ LET target == LeastLoadedNode
       IN /\ nodeLoad' = [nodeLoad EXCEPT ![target] = @ + 1]
          /\ requestQueue' = Tail(requestQueue)
          /\ routedTo' = target
          /\ UNCHANGED nodeStatus

RequestCompletes(nd) ==
    /\ nodeLoad[nd] > 0
    /\ nodeLoad' = [nodeLoad EXCEPT ![nd] = @ - 1]
    /\ UNCHANGED <<nodeStatus, requestQueue, routedTo>>

NodeDegrades(nd) ==
    /\ nodeStatus[nd] = "healthy"
    /\ nodeStatus' = [nodeStatus EXCEPT ![nd] = "degraded"]
    /\ UNCHANGED <<nodeLoad, requestQueue, routedTo>>

NodeFails(nd) ==
    /\ nodeStatus[nd] = "degraded"
    /\ nodeStatus' = [nodeStatus EXCEPT ![nd] = "offline"]
    /\ nodeLoad' = [nodeLoad EXCEPT ![nd] = 0]
    /\ UNCHANGED <<requestQueue, routedTo>>

NodeRecovers(nd) ==
    /\ nodeStatus[nd] = "offline"
    /\ nodeStatus' = [nodeStatus EXCEPT ![nd] = "healthy"]
    /\ UNCHANGED <<nodeLoad, requestQueue, routedTo>>

NodeHeals(nd) ==
    /\ nodeStatus[nd] = "degraded"
    /\ nodeStatus' = [nodeStatus EXCEPT ![nd] = "healthy"]
    /\ UNCHANGED <<nodeLoad, requestQueue, routedTo>>

Next ==
    \/ RequestArrives
    \/ RouteRequest
    \/ \E nd \in Nodes : RequestCompletes(nd)
    \/ \E nd \in Nodes : NodeDegrades(nd)
    \/ \E nd \in Nodes : NodeFails(nd)
    \/ \E nd \in Nodes : NodeRecovers(nd)
    \/ \E nd \in Nodes : NodeHeals(nd)

Spec == Init /\ [][Next]_vars

NoOverload == \A x \in Nodes : nodeLoad[x] <= MaxLoad
QueueBounded == Len(requestQueue) <= MaxQueueSize
AtLeastOneNotOffline ==
    \/ \E x \in Nodes : nodeStatus[x] /= "offline"
    \/ \A x \in Nodes : nodeStatus[x] = "offline"

=============================================================================
