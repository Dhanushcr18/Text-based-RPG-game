from flask import Flask, render_template, request, jsonify
import webbrowser
import threading
import time
import os

app = Flask(__name__)

# Game state
game_state = {
    "current_scene": "forest",
    "health": 100,
    "gold": 50,
    "inventory": ["Sword", "Potion"],
    "backgrounds": ["forest", "cave", "castle", "town"],
    "current_bg": 0
}

# Game scenes data
scenes = {
    "forest": {
        "description": "You stand at the edge of an ancient forest. The trees loom tall before you, their leaves whispering secrets in the wind.",
        "choices": [
            {"text": "Enter the forest", "next_scene": "forest_deep", "health_change": 0, "gold_change": 0},
            {"text": "Walk around the perimeter", "next_scene": "forest_path", "health_change": 0, "gold_change": 5},
            {"text": "Check your equipment", "next_scene": "forest", "health_change": 0, "gold_change": 0}
        ]
    },
    "forest_deep": {
        "description": "The forest grows darker as you venture deeper. Strange sounds echo around you. A small glint catches your eye near a mossy rock.",
        "choices": [
            {"text": "Investigate the glint", "next_scene": "forest_treasure", "health_change": -10, "gold_change": 20},
            {"text": "Continue cautiously", "next_scene": "forest_ruins", "health_change": 0, "gold_change": 0},
            {"text": "Turn back", "next_scene": "forest", "health_change": 0, "gold_change": 0}
        ]
    },
    "forest_path": {
        "description": "Following the forest's edge, you find a well-worn path leading to a small village in the distance.",
        "choices": [
            {"text": "Go to the village", "next_scene": "town", "health_change": 0, "gold_change": 0},
            {"text": "Return to the forest entrance", "next_scene": "forest", "health_change": 0, "gold_change": 0},
            {"text": "Follow a faint trail into the undergrowth", "next_scene": "first_steps", "health_change": -5, "gold_change": 0}
        ]
    },
    "first_steps": {
        "description": "The path ahead is unclear, but the call of the forest is strong. You follow a trail barely visible under the thick undergrowth, each step a carefully placed footfall. Sunlight filters through the canopy, creating an ethereal glow on the forest floor.",
        "choices": [
            {"text": "Continue deeper into the forest", "next_scene": "call_of_wild", "health_change": 0, "gold_change": 0},
            {"text": "Turn back while you still can", "next_scene": "forest", "health_change": 0, "gold_change": 0}
        ]
    },
    "call_of_wild": {
        "description": "As you venture further, the trees seem to grow even taller, their branches intertwined like protective arms. The air grows cooler, and the scent of damp earth fills your senses. You hear rustling leaves, chirping birds, and a faint melodic sound from within the forest.",
        "choices": [
            {"text": "Follow the mysterious sound", "next_scene": "mystery_deepens", "health_change": -5, "gold_change": 0},
            {"text": "Mark your location and return later", "next_scene": "forest", "health_change": 0, "gold_change": 0, "add_item": "Map to Ancient Oak"}
        ]
    },
    "mystery_deepens": {
        "description": "Suddenly, you come across a clearing bathed in unusual light. In the center stands an ancient, gnarled oak, its branches reaching skyward like a giant's fingers. You sense a watchful gaze emanating from the tree itself.",
        "choices": [
            {"text": "Approach the oak tree", "next_scene": "oak_encounter", "health_change": 0, "gold_change": 0},
            {"text": "Quickly leave the clearing", "next_scene": "forest", "health_change": -10, "gold_change": 0},
            {"text": "Examine the area cautiously", "next_scene": "oak_examination", "health_change": 0, "gold_change": 5}
        ]
    },
    "oak_encounter": {
        "description": "As you step closer, the whispers grow louder. The bark seems to shift, forming patterns that almost look like a face. A deep voice resonates in your mind: 'Who dares approach the Heartwood?'",
        "choices": [
            {"text": "Speak respectfully to the tree", "next_scene": "heartwood_dialogue", "health_change": 0, "gold_change": 0},
            {"text": "Touch the tree's bark", "next_scene": "tree_touch", "health_change": -15, "gold_change": 0},
            {"text": "Step back and apologize", "next_scene": "forest", "health_change": 0, "gold_change": 0}
        ]
    },
    "oak_examination": {
        "description": "Circling the clearing, you notice strange carvings at the oak's base. Among the roots, you find several gold coins and a silver pendant shaped like a leaf.",
        "choices": [
            {"text": "Take the coins and pendant", "next_scene": "forest", "health_change": 0, "gold_change": 25, "add_item": "Silver Leaf Pendant"},
            {"text": "Leave the offerings undisturbed", "next_scene": "forest", "health_change": 10, "gold_change": 0},
            {"text": "Place your own offering (a gold coin)", "next_scene": "forest", "health_change": 20, "gold_change": -5}
        ]
    },
    "forest_treasure": {
        "description": "You carefully move the moss aside to reveal a small chest. It's unlocked! Inside you find some gold coins and a strange-looking key.",
        "choices": [
            {"text": "Take the treasure", "next_scene": "forest", "health_change": 0, "gold_change": 30, "add_item": "Ancient Key"},
            {"text": "Leave it be", "next_scene": "forest", "health_change": 5, "gold_change": 0}
        ]
    },
    "forest_ruins": {
        "description": "Pushing through the dense foliage, you stumble upon ancient stone ruins covered in vines. There's an eerie stillness about this place.",
        "choices": [
            {"text": "Explore the ruins", "next_scene": "ruins_exploration", "health_change": -10, "gold_change": 0},
            {"text": "Mark the location on your map", "next_scene": "forest", "health_change": 0, "gold_change": 0, "add_item": "Map to Ruins"},
            {"text": "Leave quickly", "next_scene": "forest", "health_change": 0, "gold_change": 0}
        ]
    }
}

def open_browser():
    # Wait a second for the server to start
    time.sleep(1)
    webbrowser.open_new('http://127.0.0.1:5000/')

@app.route('/')
def index():
    # Serve the HTML directly
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Text-Based RPG Adventure</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: 'Georgia', serif;
                color: #fff;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #222;
                background-image: url("https://i.pinimg.com/1200x/2a/c6/9c/2ac69ccb7c141d7bfc9bb6983a58147f.jpg");
                background-size: cover;
            }

            #game-container {
                width: 800px;
                height: 600px;
                border: 3px solid #5a3e2b;
                border-radius: 10px;
                position: relative;
                overflow: hidden;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
                padding: 20px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
            }

            /* Background Themes */
            .forest-bg {
                background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                            url('https://i.pinimg.com/1200x/0e/07/80/0e0780cec5095b930a6e5043d683ec03.jpg') no-repeat center center;
                background-size: cover;
            }

            .cave-bg {
                background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                            url('https://i.pinimg.com/736x/c3/c5/e1/c3c5e1579a29a9142108b8752486f96f.jpg') no-repeat center center;
                background-size: cover;
            }

            .castle-bg {
                background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                            url('https://i.pinimg.com/736x/59/3f/57/593f575a08a78272dbaa0a1b65796d7e.jpg') no-repeat center center;
                background-size: cover;
            }

            .town-bg {
                background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                            url('https://i.pinimg.com/1200x/70/41/e9/7041e95d55782f2d9c62b97f0f95e6cf.jpg') no-repeat center center;
                background-size: cover;
            }

            #story-display {
                flex: 1;
                padding: 20px;
                background-color: rgba(0, 0, 0, 0.6);
                border-radius: 5px;
                margin-bottom: 20px;
                overflow-y: auto;
            }

            #story-text {
                line-height: 1.6;
                font-size: 18px;
            }

            #game-title {
                text-align: center;
                color: #e2b052;
                text-shadow: 2px 2px 4px #000;
                border-bottom: 2px solid #5a3e2b;
                padding-bottom: 10px;
            }

            #player-choices {
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-bottom: 20px;
            }

            .choice-btn {
                padding: 12px;
                background-color: #5a3e2b;
                color: #fff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
            }

            .choice-btn:hover {
                background-color: #7a5e4b;
            }

            #game-controls {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }

            #game-controls button {
                padding: 10px 15px;
                background-color: #3a2e2b;
                color: #fff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }

            #game-controls button:hover {
                background-color: #5a4e4b;
            }

            #player-stats {
                display: flex;
                justify-content: space-around;
                background-color: rgba(0, 0, 0, 0.6);
                padding: 10px;
                border-radius: 5px;
            }

            .stat {
                font-weight: bold;
            }

            .stat span {
                color: #e2b052;
            }

            /* Notification Styles */
            .notification {
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background-color: rgba(0, 0, 0, 0.8);
                color: #fff;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 1000;
                animation: slideIn 0.5s ease-out;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .notification.fade-out {
                animation: fadeOut 0.5s ease-out;
            }

            /* Positive notifications (gains) */
            .notification.positive {
                background-color: rgba(46, 125, 50, 0.9);
                border-left: 4px solid #81c784;
            }

            /* Negative notifications (losses) */
            .notification.negative {
                background-color: rgba(198, 40, 40, 0.9);
                border-left: 4px solid #e57373;
            }

            /* Inventory notifications */
            .notification.inventory {
                background-color: rgba(93, 64, 55, 0.9);
                border-left: 4px solid #d7ccc8;
            }

            @keyframes slideIn {
                from { 
                    top: -50px; 
                    opacity: 0; 
                }
                to { 
                    top: 20px; 
                    opacity: 1; 
                }
            }

            @keyframes fadeOut {
                from { 
                    opacity: 1; 
                }
                to { 
                    opacity: 0; 
                }
            }
        </style>
    </head>
    <body>
        <div id="game-container" class="forest-bg">
            <div id="story-display">
                <h1 id="game-title">The Forgotten Quest</h1>
                <div id="story-text">
                    <p>Welcome to your adventure! You find yourself at the edge of an ancient forest. The trees loom tall before you, their leaves whispering secrets in the wind. What will you do?</p>
                </div>
            </div>
            
            <div id="player-choices">
                <button class="choice-btn">Enter the forest</button>
                <button class="choice-btn">Walk around the perimeter</button>
                <button class="choice-btn">Check your equipment</button>
            </div>
            
            <div id="game-controls">
                <button id="bg-toggle">Change Background</button>
                <button id="save-btn">Save Game</button>
                <button id="load-btn">Load Game</button>
            </div>
            
            <div id="player-stats">
                <div class="stat">Health: <span id="health">100</span></div>
                <div class="stat">Gold: <span id="gold">50</span></div>
                <div class="stat">Inventory: <span id="inventory">Sword, Potion</span></div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // DOM elements
                const storyText = document.getElementById('story-text');
                const choiceButtons = document.getElementById('player-choices');
                const healthDisplay = document.getElementById('health');
                const goldDisplay = document.getElementById('gold');
                const inventoryDisplay = document.getElementById('inventory');
                const bgToggleBtn = document.getElementById('bg-toggle');
                const saveBtn = document.getElementById('save-btn');
                const loadBtn = document.getElementById('load-btn');
                const gameContainer = document.getElementById('game-container');

                // Game state
                let gameState = {
                    currentScene: 'forest',
                    health: 100,
                    gold: 50,
                    inventory: ['Sword', 'Potion'],
                    backgrounds: ['forest', 'cave', 'castle', 'town'],
                    currentBg: 0
                };

                // Initialize game
                loadScene(gameState.currentScene);

                // Event listeners
                bgToggleBtn.addEventListener('click', changeBackground);
                saveBtn.addEventListener('click', saveGame);
                loadBtn.addEventListener('click', loadGame);

                // Load a scene from the server
                function loadScene(sceneId) {
                    fetch(`/get_scene?scene=${sceneId}`)
                        .then(response => response.json())
                        .then(data => {
                            updateDisplay(data);
                            gameState.currentScene = sceneId;
                        })
                        .catch(error => console.error('Error loading scene:', error));
                }

                // Update the game display with new scene data
                function updateDisplay(sceneData) {
                    // Update story text
                    storyText.innerHTML = `<p>${sceneData.description}</p>`;
                    
                    // Clear existing buttons
                    choiceButtons.innerHTML = '';
                    
                    // Create new choice buttons
                    sceneData.choices.forEach(choice => {
                        const button = document.createElement('button');
                        button.className = 'choice-btn';
                        button.textContent = choice.text;
                        button.addEventListener('click', () => makeChoice(choice));
                        choiceButtons.appendChild(button);
                    });
                }

                // Handle player choice with enhanced notifications
                function makeChoice(choice) {
                    // Update game state
                    gameState.health += choice.health_change || 0;
                    gameState.gold += choice.gold_change || 0;
                    
                    // Handle inventory additions
                    if (choice.add_item) {
                        gameState.inventory.push(choice.add_item);
                        showNotification(`You obtained: ${choice.add_item}`, 'inventory');
                    }
                    
                    // Ensure health doesn't go below 0 or above 100
                    gameState.health = Math.max(0, Math.min(100, gameState.health));
                    
                    // Show health/gold change notifications
                    if (choice.health_change) {
                        const type = choice.health_change > 0 ? 'positive' : 'negative';
                        showNotification(choice.health_change > 0 ? 
                            `+${choice.health_change} Health` : 
                            `${choice.health_change} Health`, type);
                    }
                    if (choice.gold_change) {
                        const type = choice.gold_change > 0 ? 'positive' : 'negative';
                        showNotification(choice.gold_change > 0 ? 
                            `+${choice.gold_change} Gold` : 
                            `-${Math.abs(choice.gold_change)} Gold`, type);
                    }
                    
                    // Update UI
                    updateStats();
                    
                    // Load next scene
                    loadScene(choice.next_scene);
                    
                    // Send update to server
                    updateServerState();
                }

                // Show temporary notification with type styling
                function showNotification(message, type = 'normal') {
                    const notification = document.createElement('div');
                    notification.className = `notification ${type}`;
                    notification.textContent = message;
                    document.body.appendChild(notification);
                    
                    setTimeout(() => {
                        notification.classList.add('fade-out');
                        setTimeout(() => notification.remove(), 500);
                    }, 2000);
                }

                // Update player stats display
                function updateStats() {
                    healthDisplay.textContent = gameState.health;
                    goldDisplay.textContent = gameState.gold;
                    inventoryDisplay.textContent = gameState.inventory.join(', ');
                }

                // Change background theme
                function changeBackground() {
                    fetch('/next_background', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Remove all background classes
                        gameContainer.classList.remove('forest-bg', 'cave-bg', 'castle-bg', 'town-bg');
                        
                        // Add new background class
                        gameContainer.classList.add(`${data.background}-bg`);
                    })
                    .catch(error => console.error('Error changing background:', error));
                }

                // Save game state to server
                function saveGame() {
                    fetch('/update_state', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(gameState)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showNotification('Game saved successfully!', 'positive');
                        }
                    })
                    .catch(error => console.error('Error saving game:', error));
                }

                // Load game state from server
                function loadGame() {
                    fetch('/get_state')
                        .then(response => response.json())
                        .then(data => {
                            gameState = data;
                            updateStats();
                            loadScene(gameState.currentScene);
                            
                            // Set the background
                            gameContainer.classList.remove('forest-bg', 'cave-bg', 'castle-bg', 'town-bg');
                            gameContainer.classList.add(`${gameState.backgrounds[gameState.currentBg]}-bg`);
                            
                            showNotification('Game loaded successfully!', 'positive');
                        })
                        .catch(error => console.error('Error loading game:', error));
                }

                // Update server with current game state
                function updateServerState() {
                    fetch('/update_state', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(gameState)
                    })
                    .catch(error => console.error('Error updating server state:', error));
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/get_scene', methods=['GET'])
def get_scene():
    scene_id = request.args.get('scene', 'forest')
    scene = scenes.get(scene_id, scenes["forest"])
    return jsonify(scene)

@app.route('/update_state', methods=['POST'])
def update_state():
    global game_state
    data = request.json
    game_state["current_scene"] = data.get("current_scene", game_state["current_scene"])
    game_state["health"] = data.get("health", game_state["health"])
    game_state["gold"] = data.get("gold", game_state["gold"])
    game_state["inventory"] = data.get("inventory", game_state["inventory"])
    return jsonify({"status": "success"})

@app.route('/get_state', methods=['GET'])
def get_state():
    return jsonify(game_state)

@app.route('/next_background', methods=['POST'])
def next_background():
    global game_state
    game_state["current_bg"] = (game_state["current_bg"] + 1) % len(game_state["backgrounds"])
    return jsonify({"background": game_state["backgrounds"][game_state["current_bg"]]})

if __name__ == '__main__':
    # Start the browser in a separate thread
    threading.Thread(target=open_browser).start()
    app.run(debug=True)