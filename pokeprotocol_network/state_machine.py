class BattleStateMachine:
    def __init__(self, battle_engine):
        self.engine = battle_engine
        self.state = "SETUP"
        self.current_turn_data = None
        
    def transition_state(self, new_state):
        """Safely transition between states"""
        print(f"State transition: {self.state} -> {new_state}")
        self.state = new_state
        
    def handle_incoming_message(self, msg):
        """Process incoming messages based on current state"""
        msg_type = msg.get('message_type')
        
        if self.state == "SETUP":
            if msg_type == "HANDSHAKE_RESPONSE":
                self.engine.set_seed(int(msg['seed']))
                # Stay in SETUP until BATTLE_SETUP exchange
                
            elif msg_type == "BATTLE_SETUP":
                # Store opponent's Pokémon info
                opponent_pokemon = msg['pokemon_name']
                self.engine.set_pokemon("my_pokemon", opponent_pokemon)  # You'll set your Pokémon separately
                self.transition_state("WAITING_FOR_MOVE")
                
        elif self.state == "WAITING_FOR_MOVE":
            if msg_type == "ATTACK_ANNOUNCE":
                # Opponent announced their attack
                self.current_turn_data = {
                    'move_name': msg['move_name'],
                    'sequence_number': msg['sequence_number']
                }
                # Send defense announce
                self.transition_state("PROCESSING_TURN")
                return self.generate_defense_announce()
                
        elif self.state == "PROCESSING_TURN":
            if msg_type == "DEFENSE_ANNOUNCE":
                # Both players can now calculate damage
                turn_result = self.engine.handle_attack_announce(
                    self.current_turn_data['move_name'], 
                    is_opponent_attack=True
                )
                self.transition_state("AWAITING_CALCULATION")
                return self.generate_calculation_report(turn_result)
                
            elif msg_type == "CALCULATION_REPORT":
                # Compare calculations
                if self.validate_calculation_report(msg):
                    self.transition_state("CONFIRMING_CALCULATION")
                    return self.generate_calculation_confirm()
                else:
                    self.transition_state("RESOLVING_DISCREPANCY")
                    return self.generate_resolution_request()
                    
        elif self.state == "AWAITING_CALCULATION":
            if msg_type == "CALCULATION_REPORT":
                if self.validate_calculation_report(msg):
                    self.transition_state("CONFIRMING_CALCULATION")
                    return self.generate_calculation_confirm()
                else:
                    self.transition_state("RESOLVING_DISCREPANCY") 
                    return self.generate_resolution_request()
                    
        elif self.state == "CONFIRMING_CALCULATION":
            if msg_type == "CALCULATION_CONFIRM":
                # Turn completed successfully
                self.engine.is_my_turn = not self.engine.is_my_turn
                self.transition_state("WAITING_FOR_MOVE")
                self.current_turn_data = None
                
        elif self.state == "RESOLVING_DISCREPANCY":
            if msg_type == "RESOLUTION_REQUEST":
                # Handle calculation discrepancy
                return self.handle_resolution_request(msg)
            elif msg_type == "CALCULATION_CONFIRM":
                # Discrepancy resolved
                self.engine.is_my_turn = not self.engine.is_my_turn
                self.transition_state("WAITING_FOR_MOVE")
                self.current_turn_data = None
                
        elif self.state == "GAME_OVER":
            # Battle ended
            pass
            
        return None
    
    def generate_defense_announce(self):
        """Generate DEFENSE_ANNOUNCE message"""
        return {
            'message_type': 'DEFENSE_ANNOUNCE',
            'sequence_number': self.get_next_sequence_number()
        }
    
    def generate_calculation_report(self, turn_result):
        """Generate CALCULATION_REPORT message"""
        return {
            'message_type': 'CALCULATION_REPORT',
            'attacker': turn_result['attacker'],
            'move_used': turn_result['move_used'],
            'remaining_health': turn_result['remaining_health'],
            'damage_dealt': turn_result['damage_dealt'],
            'defender_hp_remaining': turn_result['defender_hp_remaining'],
            'status_message': turn_result['status_message'],
            'sequence_number': self.get_next_sequence_number()
        }
    
    def generate_calculation_confirm(self):
        """Generate CALCULATION_CONFIRM message"""
        return {
            'message_type': 'CALCULATION_CONFIRM',
            'sequence_number': self.get_next_sequence_number()
        }
    
    def generate_resolution_request(self):
        """Generate RESOLUTION_REQUEST when calculations don't match"""
        # Use our local calculation as the source of truth
        turn_result = self.engine.handle_attack_announce(
            self.current_turn_data['move_name'],
            is_opponent_attack=True
        )
        
        return {
            'message_type': 'RESOLUTION_REQUEST',
            'attacker': turn_result['attacker'],
            'move_used': turn_result['move_used'],
            'damage_dealt': turn_result['damage_dealt'],
            'defender_hp_remaining': turn_result['defender_hp_remaining'],
            'sequence_number': self.get_next_sequence_number()
        }
    
    def validate_calculation_report(self, report_msg):
        """Compare received calculation report with our local calculation"""
        local_result = self.engine.handle_attack_announce(
            self.current_turn_data['move_name'],
            is_opponent_attack=True
        )
        
        # Compare key values (allow small rounding differences)
        return (
            abs(local_result['damage_dealt'] - int(report_msg['damage_dealt'])) <= 1 and
            abs(local_result['defender_hp_remaining'] - int(report_msg['defender_hp_remaining'])) <= 1
        )
    
    def get_next_sequence_number(self):
        """Generate next sequence number (you'll replace this with network layer)"""
        import random
        return random.randint(1000, 9999)
