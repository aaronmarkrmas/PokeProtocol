import csv
import random

class Pokemon:
    def __init__(self, name, hp, attack, special_attack, defense, special_defense, type1, type2=None):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.attack = attack
        self.special_attack = special_attack
        self.defense = defense
        self.special_defense = special_defense
        self.type1 = type1
        self.type2 = type2
        self.types = [type1]
        if type2 and type2.lower() != 'nan' and type2 != '':
            self.types.append(type2)
        
    def take_damage(self, damage):
        self.current_hp = max(0, self.current_hp - damage)
        return self.current_hp <= 0  # Return True if fainted

def load_pokemon(filename):
    """Load Pokémon stats from the actual CSV format with the provided columns"""
    pokemon_data = {}
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    name = row['name']
                    
                    # Handle type2 - it might be empty or 'NaN'
                    type2 = row.get('type2', None)
                    if type2 and type2.lower() in ['', 'nan', 'none']:
                        type2 = None
                    
                    # Create Pokemon object with correct attributes
                    pokemon = Pokemon(
                        name=name,
                        hp=int(float(row['hp'])),
                        attack=int(float(row['attack'])),
                        special_attack=int(float(row['sp_attack'])),
                        defense=int(float(row['defense'])),
                        special_defense=int(float(row['sp_defense'])),
                        type1=row['type1'],
                        type2=type2
                    )
                    pokemon_data[name.lower()] = pokemon
                    
                except (KeyError, ValueError) as e:
                    print(f"Warning: Skipping invalid row {row.get('name', 'unknown')}: {e}")
                    continue
                    
        print(f"Successfully loaded {len(pokemon_data)} Pokémon from {filename}")
        return pokemon_data
        
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return {}
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

def get_sample_pokemon():
    """Fallback sample Pokémon data if CSV fails"""
    sample_data = {
        'pikachu': Pokemon('Pikachu', 35, 55, 50, 40, 50, 'Electric'),
        'charmander': Pokemon('Charmander', 39, 52, 60, 43, 50, 'Fire'),
        'squirtle': Pokemon('Squirtle', 44, 48, 50, 65, 64, 'Water'),
        'bulbasaur': Pokemon('Bulbasaur', 45, 49, 65, 49, 65, 'Grass', 'Poison')
    }
    print("Using sample Pokémon data")
    return sample_data
