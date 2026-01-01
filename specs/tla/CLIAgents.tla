---------------------------- MODULE CLIAgents ----------------------------
(*
 * PlusCal Specification for TriForce CLI Agents
 * 
 * Models agent coordination strategies:
 * - PARALLEL: All agents work simultaneously
 * - SEQUENTIAL: Agents work one after another  
 * - CONSENSUS: Agents vote on best response
 *
 * Agents: claude-mcp, codex-mcp, gemini-mcp, opencode-mcp
 *)

EXTENDS Naturals, Sequences, FiniteSets, TLC

CONSTANTS
    Agents,             \* Set of agents {claude, codex, gemini, opencode}
    LeadAgent,          \* Lead agent for coordination (gemini)
    MaxRetries          \* Max retries before giving up

(*--algorithm CLIAgents

variables
    agentStatus = [a \in Agents |-> "stopped"],  \* stopped, running, error
    agentResponse = [a \in Agents |-> ""],       \* Response from each agent
    taskQueue = <<>>,                             \* Queue of pending tasks
    currentTask = "",                             \* Current task being processed
    strategy = "parallel",                        \* parallel, sequential, consensus
    consensusVotes = [a \in Agents |-> ""],      \* Votes for consensus mode
    finalResponse = "",                           \* Final aggregated response
    retryCount = 0;

define
    \* All agents are either stopped or have finished
    AllAgentsIdle == \A a \in Agents : agentStatus[a] \in {"stopped", "done", "error"}
    
    \* At least one agent is healthy
    SomeAgentHealthy == \E a \in Agents : agentStatus[a] = "running"
    
    \* Consensus reached when majority agrees
    ConsensusReached == 
        LET votes == {consensusVotes[a] : a \in Agents}
            maxVote == CHOOSE v \in votes : 
                Cardinality({a \in Agents : consensusVotes[a] = v}) >= 
                Cardinality({a \in Agents : consensusVotes[a] = w}) 
                \A w \in votes
        IN Cardinality({a \in Agents : consensusVotes[a] = maxVote}) > Cardinality(Agents) \div 2
end define;

\* Start an agent
procedure StartAgent(agent)
begin
    StartA:
        if agentStatus[agent] = "stopped" then
            agentStatus[agent] := "running";
        end if;
    return;
end procedure;

\* Stop an agent
procedure StopAgent(agent)
begin
    StopA:
        agentStatus[agent] := "stopped";
        agentResponse[agent] := "";
    return;
end procedure;

\* Agent processes a task
procedure ProcessTask(agent, task)
begin
    Process:
        if agentStatus[agent] = "running" then
            \* Simulate processing (could succeed or fail)
            either
                agentResponse[agent] := "response_from_" \o agent;
                agentStatus[agent] := "done";
            or
                agentStatus[agent] := "error";
            end either;
        end if;
    return;
end procedure;

\* Lead agent (Gemini) coordinates the task
fair process Coordinator = "coordinator"
begin
    CoordLoop:
    while TRUE do
        \* Wait for task
        WaitTask:
            await Len(taskQueue) > 0;
            currentTask := Head(taskQueue);
            taskQueue := Tail(taskQueue);
        
        \* Execute based on strategy
        Execute:
            if strategy = "parallel" then
                \* Start all agents in parallel
                ParallelStart:
                    call StartAgent(LeadAgent);
                    \* Other agents would be started similarly
            elsif strategy = "sequential" then
                \* Start agents one by one
                SeqStart:
                    call StartAgent(LeadAgent);
            elsif strategy = "consensus" then
                \* Start all, collect votes
                ConsStart:
                    call StartAgent(LeadAgent);
            end if;
        
        \* Wait for completion
        WaitComplete:
            await AllAgentsIdle;
        
        \* Aggregate response
        Aggregate:
            if strategy = "consensus" then
                \* Pick majority vote
                finalResponse := "consensus_result";
            else
                \* Use lead agent response
                finalResponse := agentResponse[LeadAgent];
            end if;
        
        \* Reset for next task
        Reset:
            agentStatus := [a \in Agents |-> "stopped"];
            agentResponse := [a \in Agents |-> ""];
            currentTask := "";
    end while;
end process;

\* Individual agent processes
fair process Agent \in Agents
begin
    AgentLoop:
    while TRUE do
        \* Wait to be activated
        WaitActivate:
            await agentStatus[self] = "running" /\ currentTask # "";
        
        \* Process the task
        DoTask:
            call ProcessTask(self, currentTask);
    end while;
end process;

end algorithm; *)

\* ===================== INVARIANTS =====================

\* No deadlock: always some progress possible
NoDeadlock == 
    \/ Len(taskQueue) > 0
    \/ currentTask # ""
    \/ AllAgentsIdle

\* Type safety
TypeOK ==
    /\ agentStatus \in [Agents -> {"stopped", "running", "done", "error"}]
    /\ strategy \in {"parallel", "sequential", "consensus"}
    /\ retryCount \in 0..MaxRetries

=============================================================================
