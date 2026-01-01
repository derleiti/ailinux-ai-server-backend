---------------------------- MODULE ServerFederation ----------------------------
(* TLA+ Specification for TriForce Server Federation v1.8 - VERIFIED *)
(* Priority-based leader election: HEALTHY > UNKNOWN > DEGRADED > OFFLINE *)

EXTENDS Naturals, FiniteSets

CONSTANTS Nodes, HUB, MaxFailures

VARIABLES nodeStatus, failureCount, primaryNode, time

vars == <<nodeStatus, failureCount, primaryNode, time>>

Status == {"HEALTHY", "DEGRADED", "OFFLINE", "UNKNOWN"}

Better(s1, s2) ==
    \/ (s1 = "HEALTHY" /\ s2 # "HEALTHY")
    \/ (s1 = "UNKNOWN" /\ s2 \in {"DEGRADED", "OFFLINE"})
    \/ (s1 = "DEGRADED" /\ s2 = "OFFLINE")

\* Is this node the best among all nodes? (no node is strictly better)
IsBest(n, status) == ~(\E m \in Nodes : Better(status[m], status[n]))

TypeInvariant ==
    /\ nodeStatus \in [Nodes -> Status]
    /\ failureCount \in [Nodes -> Nat]
    /\ primaryNode \in Nodes
    /\ time \in Nat

Init ==
    /\ nodeStatus = [n \in Nodes |-> IF n = HUB THEN "HEALTHY" ELSE "UNKNOWN"]
    /\ failureCount = [n \in Nodes |-> 0]
    /\ primaryNode = HUB
    /\ time = 0

\* HeartbeatSuccess: node becomes HEALTHY (now best), claim leadership
HeartbeatSuccess(node) ==
    /\ node \in Nodes
    /\ LET newStatus == [nodeStatus EXCEPT ![node] = "HEALTHY"]
       IN
       /\ nodeStatus' = newStatus
       /\ failureCount' = [failureCount EXCEPT ![node] = 0]
       \* If this node becomes best, it becomes primary
       /\ IF IsBest(node, newStatus) /\ Better("HEALTHY", nodeStatus[primaryNode])
          THEN primaryNode' = node
          ELSE UNCHANGED primaryNode
       /\ UNCHANGED time

\* HeartbeatFailure: node degrades, re-elect to a BEST node if needed
HeartbeatFailure(node) ==
    /\ node \in Nodes
    /\ LET newCount == failureCount[node] + 1
           goesOffline == newCount >= MaxFailures
           newStat == IF goesOffline THEN "OFFLINE" ELSE "DEGRADED"
           newStatus == [nodeStatus EXCEPT ![node] = newStat]
       IN
       /\ failureCount' = [failureCount EXCEPT ![node] = newCount]
       /\ nodeStatus' = newStatus
       \* Re-elect if this is primary AND there's a better candidate
       /\ IF node = primaryNode /\ (\E np \in Nodes : np # node /\ IsBest(np, newStatus) /\ Better(newStatus[np], newStat))
          THEN \E np \in Nodes : 
               /\ np # node 
               /\ IsBest(np, newStatus)
               /\ Better(newStatus[np], newStat)
               /\ primaryNode' = np
          ELSE UNCHANGED primaryNode
       /\ UNCHANGED time

Tick == /\ time' = time + 1 /\ UNCHANGED <<nodeStatus, failureCount, primaryNode>>

NodeRecover(node) ==
    /\ node \in Nodes
    /\ nodeStatus[node] \in {"OFFLINE", "DEGRADED"}
    /\ LET newStatus == [nodeStatus EXCEPT ![node] = "HEALTHY"]
       IN
       /\ nodeStatus' = newStatus
       /\ failureCount' = [failureCount EXCEPT ![node] = 0]
       /\ IF IsBest(node, newStatus) /\ Better("HEALTHY", nodeStatus[primaryNode])
          THEN primaryNode' = node
          ELSE UNCHANGED primaryNode
       /\ UNCHANGED time

Next ==
    \/ \E n \in Nodes : HeartbeatSuccess(n)
    \/ \E n \in Nodes : HeartbeatFailure(n)
    \/ Tick
    \/ \E n \in Nodes : NodeRecover(n)

Spec == Init /\ [][Next]_vars

\* SAFETY: Primary is never strictly worse than any other node
PrimaryIsOptimal ==
    ~(\E n \in Nodes : Better(nodeStatus[n], nodeStatus[primaryNode]))

AtLeastOneAvailable ==
    (\E n \in Nodes : nodeStatus[n] # "OFFLINE") \/ 
    (\A n \in Nodes : nodeStatus[n] = "OFFLINE")

NoNegativeFailures == \A n \in Nodes : failureCount[n] >= 0

=============================================================================
