import sys
import logging
from src.engine import PredictionEngine
from src.cli import CLI, Colors

# Disable logging to avoid cluttering the interactive terminal
logging.getLogger("src").setLevel(logging.WARNING)

def main():
    print(f"{Colors.OKBLUE}Initializing Prediction Engine...{Colors.ENDC}")
    try:
        # Load the engine (datasets and indexes)
        engine = PredictionEngine().load()
    except Exception as e:
        print(f"{Colors.FAIL}Failed to load prediction engine: {e}{Colors.ENDC}")
        sys.exit(1)
        
    cli = CLI(
        prompt="router> ", 
        welcome_message="Interactive Message Router CLI initialized."
    )
    
    def cmd_predict(args: list) -> None:
        if not args:
            print(f"{Colors.WARNING}Usage: predict <message_id>{Colors.ENDC}")
            return
            
        message_id = args[0]
        
        # Locate the message in incoming_messages
        df = engine.incoming_messages
        matches = df[df['message_id'] == message_id]
        
        if matches.empty:
            print(f"{Colors.FAIL}Error: Message '{message_id}' not found in dataset.{Colors.ENDC}")
            return
            
        # Get the first match as a dict
        message_dict = matches.iloc[0].to_dict()
        
        # Route the message using the engine's public API
        result = engine.route(message_dict)
        
        # Display the formatted output
        print(f"\n{Colors.BOLD}--- Prediction Results for {message_id} ---{Colors.ENDC}")
        
        # Show truncated message text for context
        text = str(message_dict.get('message_text', ''))
        if len(text) > 80:
            text = text[:77] + "..."
        print(f"{Colors.OKCYAN}Message:     {Colors.ENDC}{text}")
        
        # Colorize the action
        action = result.get('action', '')
        if action == 'notify':
            action_color = Colors.OKGREEN
        elif action == 'mute':
            action_color = Colors.FAIL
        else:
            action_color = Colors.OKBLUE
            
        print(f"{Colors.OKCYAN}Action:      {action_color}{action.upper()}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Type:        {Colors.ENDC}{result.get('message_type', '')}")
        print(f"{Colors.OKCYAN}Confidence:  {Colors.ENDC}{result.get('confidence', 0.0)}")
        print(f"{Colors.OKCYAN}Reason:      {Colors.ENDC}{result.get('reason', '')}")
        
        # Format evidence IDs
        evidence = result.get('evidence_message_ids', [])
        evidence_str = ", ".join(map(str, evidence)) if evidence else "None"
        print(f"{Colors.OKCYAN}Evidence:    {Colors.ENDC}{evidence_str}\n")

    def cmd_explain(args: list) -> None:
        if not args:
            print(f"{Colors.WARNING}Usage: explain <message_id>{Colors.ENDC}")
            return
            
        message_id = args[0]
        
        df = engine.incoming_messages
        matches = df[df['message_id'] == message_id]
        
        if matches.empty:
            print(f"{Colors.FAIL}Error: Message '{message_id}' not found in dataset.{Colors.ENDC}")
            return
            
        message_dict = matches.iloc[0].to_dict()
        
        # Route the message with explain=True
        result = engine.route(message_dict, explain=True)
        explanation = result.get("_explanation", {})
        
        if not explanation:
            print(f"{Colors.FAIL}Error: No explanation generated.{Colors.ENDC}")
            return
            
        print(f"\n{Colors.BOLD}=== EXPLANATION FOR {message_id} ==={Colors.ENDC}")
        
        # 1. Features
        print(f"\n{Colors.HEADER}1. Detected Features{Colors.ENDC}")
        features = explanation.get("features", {})
        bool_features = [k for k, v in features.items() if isinstance(v, bool) and v]
        print(f"  Keywords: {', '.join(features.get('keywords', [])) or 'None'}")
        print(f"  Flags:    {', '.join(bool_features) or 'None'}")
        
        # 2. History & Relationships
        print(f"\n{Colors.HEADER}2. History & Context{Colors.ENDC}")
        history = explanation.get("history", {})
        print("  User Stats:")
        for k, v in history.get("user", {}).items():
            print(f"    - {k}: {v}")
        
        if history.get("sender", {}).get("has_interaction"):
            print("  Sender Interaction:")
            for k, v in history.get("sender", {}).items():
                print(f"    - {k}: {v}")
        else:
            print("  Sender: No prior interaction.")
            
        if history.get("business", {}).get("relationship") != "unknown":
            print("  Business Relationship:")
            for k, v in history.get("business", {}).items():
                print(f"    - {k}: {v}")
        
        # 3. Rules & Scores
        print(f"\n{Colors.HEADER}3. Matched Rules{Colors.ENDC}")
        matched_rules = explanation.get("matched_rules", [])
        if not matched_rules:
            print("  None. Fell through to default.")
        else:
            for r in matched_rules:
                marker = "*" if r == explanation.get("winning_rule") else " "
                print(f"  [{marker}] {Colors.OKGREEN}{r.get('rule_name')}{Colors.ENDC}: {r.get('score')} pts")
                print(f"      Action: {r.get('action')}, Type: {r.get('message_type')}")
                print(f"      Reason: {r.get('reason')}")
        
        # 4. Final Decision Path
        print(f"\n{Colors.HEADER}4. Decision Path & Confidence{Colors.ENDC}")
        print(f"  Winning Rule: {explanation.get('winning_rule', {}).get('rule_name', 'DEFAULT')}")
        print(f"  Base Score:   {abs(explanation.get('base_score', 0))}")
        print(f"  Mapped Conf:  {result.get('confidence')}")
        print(f"  Final Action: {Colors.BOLD}{result.get('action').upper()}{Colors.ENDC}")
        print(f"  Final Type:   {result.get('message_type')}")
        print(f"  Final Reason: {result.get('reason')}")
        
        evidence = result.get('evidence_message_ids', [])
        print(f"  Evidence IDs: {', '.join(map(str, evidence)) if evidence else 'None'}")
        print()

    def cmd_inspect(args: list) -> None:
        if len(args) < 2:
            print(f"{Colors.WARNING}Usage: inspect <type> <user_id> [secondary_id]{Colors.ENDC}")
            print("Types: user, sender, group, business")
            print("Examples:")
            print("  inspect user u_001")
            print("  inspect sender u_001 u_002")
            print("  inspect business u_001 business_001")
            print("  inspect group u_001 group_001")
            return
            
        entity_type = args[0].lower()
        user_id = args[1]
        
        from src.history import get_user_history, get_sender_history, get_group_history, get_business_history
        
        print(f"\n{Colors.BOLD}=== INSPECT: {entity_type.upper()} ==={Colors.ENDC}")
        
        if entity_type == "user":
            data = get_user_history(user_id)
        elif entity_type == "sender":
            if len(args) < 3:
                print(f"{Colors.FAIL}Error: inspect sender requires <user_id> <sender_id>{Colors.ENDC}")
                return
            data = get_sender_history(user_id, args[2])
        elif entity_type == "business":
            if len(args) < 3:
                print(f"{Colors.FAIL}Error: inspect business requires <user_id> <business_id>{Colors.ENDC}")
                return
            data = get_business_history(user_id, args[2])
        elif entity_type == "group":
            if len(args) < 3:
                print(f"{Colors.FAIL}Error: inspect group requires <user_id> <group_id>{Colors.ENDC}")
                return
            data = get_group_history(user_id, args[2])
        else:
            print(f"{Colors.FAIL}Error: Unknown inspect type '{entity_type}'{Colors.ENDC}")
            return
            
        for key, value in data.items():
            print(f"  {Colors.OKCYAN}{key:<25}{Colors.ENDC} : {value}")
        print()

    def cmd_analytics(args: list) -> None:
        if not args:
            print(f"{Colors.WARNING}Usage: analytics <command>{Colors.ENDC}")
            print("Commands: stats, distribution, top-businesses, top-groups, confidence, reports")
            return
            
        subcmd = args[0].lower()
        import pandas as pd
        import os
        
        output_file = engine.output_path
        if not os.path.exists(output_file):
            print(f"{Colors.FAIL}Error: {output_file} not found.{Colors.ENDC}")
            return
            
        out_df = pd.read_csv(output_file)
        in_df = engine.incoming_messages
        
        if out_df.empty:
            print(f"{Colors.FAIL}Error: Output file is empty.{Colors.ENDC}")
            return
            
        # Merge to get business_id and group_id
        merged = pd.merge(out_df, in_df, on='message_id', how='left')
        
        print(f"\n{Colors.BOLD}=== ANALYTICS: {subcmd.upper()} ==={Colors.ENDC}")
        
        if subcmd == "stats":
            total = len(out_df)
            actions = out_df['action'].value_counts()
            print(f"Total Predictions: {total}")
            print(f"Notify: {actions.get('notify', 0)} ({(actions.get('notify', 0)/total)*100:.1f}%)")
            print(f"Digest: {actions.get('digest', 0)} ({(actions.get('digest', 0)/total)*100:.1f}%)")
            print(f"Mute:   {actions.get('mute', 0)} ({(actions.get('mute', 0)/total)*100:.1f}%)")
            
        elif subcmd == "distribution":
            dist = out_df.groupby(['action', 'message_type']).size().unstack(fill_value=0)
            print("Message Type Distribution by Action:")
            print(dist.to_string())
            
        elif subcmd == "top-businesses":
            biz = merged.dropna(subset=['business_id'])
            if biz.empty:
                print("No business messages found.")
            else:
                top = biz['business_id'].value_counts().head(10)
                print("Top Businesses by Message Volume:")
                for b_id, count in top.items():
                    print(f"  {b_id}: {count} messages")
                    
        elif subcmd == "top-groups":
            grp = merged.dropna(subset=['group_id'])
            if grp.empty:
                print("No group messages found.")
            else:
                top = grp['group_id'].value_counts().head(10)
                print("Top Groups by Message Volume:")
                for g_id, count in top.items():
                    print(f"  {g_id}: {count} messages")
                    
        elif subcmd == "confidence":
            avg = out_df.groupby('action')['confidence'].mean().round(3)
            print("Average Confidence by Action:")
            for action, conf in avg.items():
                print(f"  {action.upper():<8}: {conf}")
                
        elif subcmd == "reports":
            spam = out_df[out_df['message_type'].isin(['spam', 'scam'])]
            print(f"Total Spam/Scam Detected: {len(spam)}")
            if not spam.empty:
                print("\nBreakdown by Reason:")
                print(spam['reason'].value_counts().to_string())
                
        else:
            print(f"{Colors.FAIL}Unknown analytics command: {subcmd}{Colors.ENDC}")
            
        print()

    def cmd_simulate(args: list) -> None:
        print(f"\n{Colors.BOLD}=== SIMULATE INCOMING MESSAGE ==={Colors.ENDC}")
        print("Enter message details (leave blank for defaults).")
        
        sender = input(f"{Colors.OKCYAN}Sender ID (e.g. u_011 or Dad): {Colors.ENDC}").strip()
        conv_type = input(f"{Colors.OKCYAN}Conversation (personal/group/business_update/spam): {Colors.ENDC}").strip()
        print(f"{Colors.OKCYAN}Message text:{Colors.ENDC}")
        message_text = input("> ").strip()
        
        # Build mock dictionary
        mock_msg = {
            'message_id': 'sim_001',
            'user_id': 'sim_user',
            'sender_user_id': sender or 'unknown_sender',
            'conversation_type': conv_type or 'personal',
            'message_text': message_text,
            'forwarded_count': 0,
            'media_type': None,
            'business_id': None,
            'group_id': None
        }
        
        if conv_type == 'business_update':
            mock_msg['business_id'] = sender or 'unknown_business'
        elif conv_type == 'group':
            mock_msg['group_id'] = sender or 'unknown_group'
            
        print(f"\n{Colors.OKBLUE}Routing message...{Colors.ENDC}")
        result = engine.route(mock_msg, explain=True)
        
        print(f"\n{Colors.BOLD}--- Prediction Results ---{Colors.ENDC}")
        action = result.get('action', '')
        if action == 'notify':
            action_color = Colors.OKGREEN
        elif action == 'mute':
            action_color = Colors.FAIL
        else:
            action_color = Colors.OKBLUE
            
        print(f"{Colors.OKCYAN}Action:      {action_color}{action.upper()}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Type:        {Colors.ENDC}{result.get('message_type', '')}")
        print(f"{Colors.OKCYAN}Confidence:  {Colors.ENDC}{result.get('confidence', 0.0)}")
        print(f"{Colors.OKCYAN}Reason:      {Colors.ENDC}{result.get('reason', '')}")
        
        explanation = result.get("_explanation", {})
        if explanation:
            winning_rule = explanation.get('winning_rule', {})
            rule_name = winning_rule.get('rule_name', 'DEFAULT') if winning_rule else 'DEFAULT'
            print(f"{Colors.OKCYAN}Rule Fired:  {Colors.ENDC}{rule_name}")
        print()

    def cmd_debug(args: list) -> None:
        if not args:
            print(f"{Colors.WARNING}Usage: debug <message_id>{Colors.ENDC}")
            return
            
        message_id = args[0]
        
        df = engine.incoming_messages
        matches = df[df['message_id'] == message_id]
        
        if matches.empty:
            print(f"{Colors.FAIL}Error: Message '{message_id}' not found in dataset.{Colors.ENDC}")
            return
            
        message_dict = matches.iloc[0].to_dict()
        
        print(f"\n{Colors.BOLD}=== DEBUG EXECUTION TRACE: {message_id} ==={Colors.ENDC}")
        
        # Route the message with explain=True
        result = engine.route(message_dict, explain=True)
        explanation = result.get("_explanation", {})
        
        if not explanation or "rule_traces" not in explanation:
            print(f"{Colors.FAIL}Error: No rule trace available.{Colors.ENDC}")
            return
            
        rule_traces = explanation.get("rule_traces", [])
        winning_rule = explanation.get('winning_rule', {})
        winning_rule_name = winning_rule.get('rule_name') if winning_rule else None
        
        print(f"{Colors.OKCYAN}{'RULE NAME':<25} | {'MATCHED':<7} | {'SCORE':<6} | {'TIME (ms)':<9} | {'WINNER'} | {'REASON'}{Colors.ENDC}")
        print("-" * 100)
        
        for trace in rule_traces:
            rule_name = trace['rule_name']
            matched = "YES" if trace['matched'] else "no"
            score = str(trace['score']) if trace['score'] is not None else "-"
            time_ms = f"{trace['time_ms']:.3f}"
            is_winner = "<- WINNER" if rule_name == winning_rule_name else ""
            reason = trace['reason'] if trace['matched'] else ""
            
            color = Colors.OKGREEN if trace['matched'] else Colors.ENDC
            if rule_name == winning_rule_name:
                color = Colors.BOLD + Colors.HEADER
                
            print(f"{color}{rule_name:<25} | {matched:<7} | {score:<6} | {time_ms:<9} | {is_winner:<8} | {reason}{Colors.ENDC}")
            
        print(f"\n{Colors.OKBLUE}Total Rules Executed: {len(rule_traces)}{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Total Rule Execution Time: {sum(t['time_ms'] for t in rule_traces):.3f} ms{Colors.ENDC}\n")

    def cmd_insights(args: list) -> None:
        if not args:
            print(f"{Colors.WARNING}Usage: insights <message_id>{Colors.ENDC}")
            return
            
        message_id = args[0]
        
        df = engine.incoming_messages
        matches = df[df['message_id'] == message_id]
        
        if matches.empty:
            print(f"{Colors.FAIL}Error: Message '{message_id}' not found in dataset.{Colors.ENDC}")
            return
            
        message_dict = matches.iloc[0].to_dict()
        
        print(f"\n{Colors.BOLD}=== AI ROUTING INSIGHT: {message_id} ==={Colors.ENDC}")
        
        # Route the message with explain=True
        result = engine.route(message_dict, explain=True)
        explanation = result.get("_explanation", {})
        
        if not explanation:
            print(f"{Colors.FAIL}Error: No routing explanation available.{Colors.ENDC}")
            return
            
        action = result.get("action", "unknown").upper()
        confidence = result.get("confidence", 0.0)
        winner = explanation.get("winning_rule", {})
        winner_name = winner.get("rule_name", "the default fallback") if winner else "the default fallback"
        reason = result.get("reason", "").strip()
        if reason.endswith('.'):
            reason = reason[:-1]
            
        history = explanation.get("history", {})
        sender_hist = history.get("sender", {})
        biz_hist = history.get("business", {})
        grp_hist = history.get("group", {})
        features = explanation.get("features", {})
        matched_rules = explanation.get("matched_rules", [])
        
        parts = []
        # 1. Core decision
        parts.append(f"The system decided to {Colors.BOLD}{action}{Colors.ENDC} this message with {confidence*100:.0f}% confidence.")
        
        # 2. Primary reason
        if reason:
            reason_lower = reason[:1].lower() + reason[1:]
            parts.append(f"The primary driver was `{winner_name}`, which flagged that {reason_lower}.")
            
        # 3. Contextual modifiers
        context = []
        if sender_hist.get("has_been_reported"):
            context.append("the sender has been reported previously")
        elif sender_hist.get("has_ignored"):
            context.append("you typically ignore this sender")
        elif sender_hist.get("has_replied_recently"):
            context.append("you have recently replied to this sender")
            
        if biz_hist.get("is_verified"):
            if biz_hist.get("has_ordered_recently"):
                context.append("it comes from a verified business you recently ordered from")
            else:
                context.append("it is a verified business but lacks recent engagement")
                
        if grp_hist.get("is_muted"):
            context.append("the group is currently muted")
            
        if features.get("is_forwarded"):
            f_count = message_dict.get("forwarded_count", 0)
            context.append(f"the message was forwarded {f_count} times")
            
        if features.get("contains_urgent"):
            context.append("it contains urgent keywords")
            
        if context:
            parts.append(f"Contextual factors heavily influenced this decision: {', and '.join(context)}.")
            
        # 4. Suppressed/overridden rules
        losers = [r for r in matched_rules if r.get("rule_name") != winner_name]
        if losers:
            loser_names = ", ".join([r.get("rule_name") for r in losers])
            parts.append(f"Although other rules matched ({loser_names}), they were overridden by the final priority resolution.")
            
        # Format and print with textwrap
        import textwrap
        full_text = " ".join(parts)
        wrapped = textwrap.fill(full_text, width=80)
        print(f"\n{wrapped}\n")

    # Register the commands
    cli.register(
        "predict", 
        cmd_predict, 
        "Route a specific message_id through the prediction engine"
    )
    
    cli.register(
        "explain",
        cmd_explain,
        "Show detailed tracing and intermediate state for a prediction"
    )
    
    cli.register(
        "debug",
        cmd_debug,
        "Display rule execution trace and performance metrics for a message"
    )
    
    cli.register(
        "insights",
        cmd_insights,
        "Generate a human-readable summary of why a prediction was made"
    )
    
    cli.register(
        "inspect",
        cmd_inspect,
        "Inspect historical statistics for user, sender, business, or group"
    )
    
    cli.register(
        "analytics",
        cmd_analytics,
        "Display aggregated statistics (stats, distribution, top-businesses, top-groups, confidence, reports)"
    )
    
    cli.register(
        "simulate",
        cmd_simulate,
        "Simulate routing a custom typed message"
    )
    
    # Start the interactive loop
    cli.run()

if __name__ == "__main__":
    main()
