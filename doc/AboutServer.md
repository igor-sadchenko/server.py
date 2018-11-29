# About Game Server

## Client-Server messages

### Common message format

The client sends to the server some "action" messages and retrieves "response" messages. Byte order: **little**.

An **action message** always begins from the action code (4 bytes). All possible action codes can be represented by enumeration (C++):

```C++
enum Action
{
    LOGIN = 1,
    LOGOUT = 2,
    MOVE = 3,
    UPGRADE = 4,
    TURN = 5,
    PLAYER = 6,
    MAP = 10
}
```

The **data section** follows after the action code.

**Data section** format:
**{data length (4 bytes)} + {bytes of UTF-8 string with data in JSON format}**

Client gets a **response message** as answer from the server. A response message starts with **result code**:

```C++
enum Result
{
    OKEY = 0,
    BAD_COMMAND = 1,
    RESOURCE_NOT_FOUND = 2,
    ACCESS_DENIED = 3,
    INAPPROPRIATE_GAME_STATE = 4,
    TIMEOUT = 5,
    INTERNAL_SERVER_ERROR = 500
}
```

The **data section** of the response follows after the result code.


Full **client-server message** format:
**{action (4 bytes)} + {data length (4 bytes)} + {bytes of UTF-8 string with data in JSON format}**

So client-server messages can be represented by following types:

```C++
struct ActionMessage
{
    Action actionCode;
    size_t dataLength;
    char data[];
}

struct ResposeMessage
{
    Result result;
    size_t dataLength;
    char data[];
}
```

### LOGIN action

This action message has to be the first in a client-server "dialog".

The server expects to receive following required values:

* **name** - player's name

Also following values are not required:

* **password** - player's password used to verify the connection, if player with the same name tries to connect with another password - login will be rejected

For multi-play game you have to define additional values:

* **num_players** - number of players in the game
* **game** - game's name

#### Example: LOGIN request
    
    b'\x01\x00\x00\x00\x10\x00\x00\x00{"name":"Boris"}'
    
    |action|msg length|msg             |
    |------|----------|----------------|
    |1     |16        |{"name":"Boris"}|

#### Example: LOGIN response message

``` JSON
{
    "home": {
        "idx": 1,
        "post_idx": 1
    },
    "idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
    "in_game": true,
    "name": "Boris",
    "rating": 0,
    "town": {
        "armor": 100,
        "armor_capacity": 200,
        "events": [],
        "idx": 1,
        "level": 1,
        "name": "Minsk",
        "next_level_price": 100,
        "player_idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
        "point_idx": 1,
        "population": 1,
        "population_capacity": 10,
        "product": 200,
        "product_capacity": 200,
        "train_cooldown": 2,
        "type": 1
    },
    "trains": [
        {
            "cooldown": 0,
            "events": [],
            "fuel": 400,
            "fuel_capacity": 400,
            "fuel_consumption": 1,
            "goods": 0,
            "goods_capacity": 40,
            "goods_type": null,
            "idx": 1,
            "level": 1,
            "line_idx": 1,
            "next_level_price": 40,
            "player_idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
            "position": 0,
            "speed": 0
        },
        ...
    ]
}
```

Some fields from LOGIN response:

* **home.idx** - home's point index on the map
* **home.post_idx** - home's post index on the map
* **idx** - player's unique index
* **name** - player's name
* **rating** - player's rating shows his progress in the game
* **town** - home's post data
* **trains** - list of trains belong to the player

### PLAYER action

This action reads information about the player. Schema of the response message is the same as response on login.

The action does not require any data.

#### Example: PLAYER request

    b'\x06\x00\x00\x00\x00\x00\x00\x00'
    
    |action|msg length|msg|
    |------|----------|---|
    |6     |0         |   |

#### Example: PLAYER response message

``` JSON
{
    "home": {
        "idx": 1,
        "post_idx": 1
    },
    "idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
    "in_game": true,
    "name": "Boris",
    "rating": 0,
    "town": {
        "armor": 100,
        "armor_capacity": 200,
        "events": [],
        "idx": 1,
        "level": 1,
        "name": "Minsk",
        "next_level_price": 100,
        "player_idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
        "point_idx": 1,
        "population": 1,
        "population_capacity": 10,
        "product": 200,
        "product_capacity": 200,
        "train_cooldown": 2,
        "type": 1
    },
    "trains": [
        {
            "cooldown": 0,
            "events": [],
            "fuel": 400,
            "fuel_capacity": 400,
            "fuel_consumption": 1,
            "goods": 0,
            "goods_capacity": 40,
            "goods_type": null,
            "idx": 1,
            "level": 1,
            "line_idx": 1,
            "next_level_price": 40,
            "player_idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
            "position": 0,
            "speed": 0
        },
        ...
    ]
}
```

### LOGOUT action

This action closes connection.

The action does not require any data.

#### Example: LOGOUT request

    b'\x02\x00\x00\x00\x00\x00\x00\x00'
    
    |action|msg length|msg|
    |------|----------|---|
    |2     |0         |   |

### MAP action

This action reads the game map. The game map is divided into layers:

* Layer 0 - static objects: 'idx', 'name', 'points', 'lines'
* Layer 1 - dynamic objects: 'idx', 'posts', 'trains', 'ratings'
* Layer 10 - coordinates of points: 'idx', 'size', 'coordinates'

The server expects to receive following required values:

* **layer** - map's layer number

#### Example: MAP request

    b'\x02\x00\x00\x00\x0b\x00\x00\x00{"layer":0}'
    
    |action|msg length|msg        |
    |------|----------|-----------|
    |10    |11        |{"layer":0}|

#### Example: MAP response message (for layer 0)

``` JSON
{
    "idx": 1,
    "lines": [
        {
            "idx": 192,
            "length": 1,
            "points": [
                112,
                107
            ]
        },
        {
            "idx": 193,
            "length": 2,
            "points": [
                101,
                102
            ]
        },
        ...
    ],
    "name": "map01",
    "points": [
        {
            "idx": 101,
            "post_idx": 13
        },
        {
            "idx": 102,
            "post_idx": null
        },
        ...
    ]
}
```

#### Example: MAP response message (for layer 1)

``` JSON
{
    "idx": 1,
    "posts": [
        {
            "events": [],
            "idx": 17,
            "name": "market-small",
            "point_idx": 107,
            "product": 5,
            "product_capacity": 5,
            "replenishment": 1,
            "type": 2
        },
        {
            "armor": 3,
            "armor_capacity": 200,
            "events": [],
            "idx": 13,
            "level": 1,
            "name": "Minsk",
            "next_level_price": 100,
            "player_idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
            "point_idx": 101,
            "population": 3,
            "population_capacity": 10,
            "product": 60,
            "product_capacity": 200,
            "train_cooldown": 2,
            "type": 1
        },
        {
            "armor": 48,
            "armor_capacity": 48,
            "events": [],
            "idx": 18,
            "name": "storage-big",
            "point_idx": 106,
            "replenishment": 2,
            "type": 3
        },
        ...
    ],
    "ratings": {
        "a33dc107-04ab-4039-9578-1dccd00867d1": {
            "idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
            "name": "Boris",
            "rating": 0
        }
    },
    "trains": [
        {
            "cooldown": 0,
            "events": [],
            "fuel": 400,
            "fuel_capacity": 400,
            "fuel_consumption": 1,
            "goods": 0,
            "goods_capacity": 40,
            "goods_type": null,
            "idx": 1,
            "level": 1,
            "line_idx": 193,
            "next_level_price": 40,
            "player_idx": "a33dc107-04ab-4039-9578-1dccd00867d1",
            "position": 0,
            "speed": 0
        },
        ...
    ]
}
```

Each **post** has following key fields:

* **idx** - unique post index
* **name** - post's name
* **type** - post's type

Each **train** has following key fields:

* **idx** - unique train index
* **line_idx** - line index where the train moves in the current moment
* **player_idx** - index of the player, who is an owner of the train
* **position** - position of the train on the current line
* **speed** - speed of the train

Field **ratings** contains ratings of all players in the game. The rating is recalculated on every turn.

#### Example: MAP response message (for layer 10)

``` JSON
{
    "coordinates": [
        {
            "idx": 101,
            "x": 75,
            "y": 16
        },
        {
            "idx": 102,
            "x": 250,
            "y": 16
        },
        ...
    ],
    "idx": 2,
    "size": [
        330,
        248
    ]
}
```

Layer 10 contains coordinates for all points on the map. Also layer 10 contains size of the map.

Each item in **coordinates** includes:

* **idx** - point index
* **x** - x coordinate
* **y** - y coordinate

Field **size** is array of two integers: **width** and **height**.

### MOVE action

This action moves the train on the game map: changes speed, direction, line.

The server expects to receive following required values:

* **line_idx** - index of the line where the train should be placed on next turn
* **speed** - speed of the train, possible values:
  * 0 - the train will be stopped
  * 1 - the train will move in positive direction
  * -1 - the train will move in negative direction
* **train_idx** - index of the train

#### Example: MOVE request

    b'\x03\x00\x00\x00(\x00\x00\x00{"line_idx":193,"speed":1,"train_idx":1}'
    
    |action|msg length|msg                                     |
    |------|----------|----------------------------------------|
    |3     |40        |{"line_idx":193,"speed":1,"train_idx":1}|

### UPGRADE action

This action upgrades trains and posts to the next level.

The server expects to receive following required values:

* **posts** - list with indexes of posts to upgrade
* **trains** - list with indexes of trains to upgrade

#### Example: UPGRADE request

    b'\x04\x00\x00\x00\x19\x00\x00\x00{"posts":[],"trains":[1]}'
    
    |action|msg length|msg                      |
    |------|----------|-------------------------|
    |4     |25        |{"posts":[],"trains":[1]}|

### TURN action

This action is needed to force next turn of the game, it allows you to not wait for game's time slice and play faster.
The game time slice equals to 10 seconds.

The action does not require any data.

#### Example: TURN request

    b'\x05\x00\x00\x00\x00\x00\x00\x00'
    
    |action|msg length|msg|
    |------|----------|---|
    |5     |0         |   |

## About the Game

### Two types of goods

There are two types of resources (goods) in the game: product and armor.

### Three types of posts

Posts are points of interest on the game map. There are three types of posts: TOWN, MARKET, STORAGE.

```C++
enum PostType
{
    TOWN = 1,
    MARKET = 2,
    STORAGE = 3
}
```

### Product

This type of resource (goods) is used to support the city's population. During a game turn 1 settler eats 1 product in the town.
Product can be mined by a train in a market (on the map this object is defined as post with type of MARKET).
Products sometimes can be stolen by parasites (see: "Parasites Invasion").

### Armor

This type of resource (goods) is used to increase the town's defence from bandits attack (see: "Bandits Attack").
Also armor can be used to upgrade units (see: "Upgrade"). Bandits attack decreases armor in the town (1 bandit -> -1 armor).
Armor can be mined by a train in a storage (on the map this object is defined as post with type STORAGE).
If you have enough armor in the town - you can use it to upgrade the town itself or/and upgrade your train(s).

### Events

Sometimes something can happens in the game :). Player will be notified about it with the using of events.
Each event is bound to some game entity (town, train, etc.).
There are following event types in the game:

```C++
enum EventType
{
    TRAIN_COLLISION = 1,
    HIJACKERS_ASSAULT = 2,
    PARASITES_ASSAULT = 3,
    REFUGEES_ARRIVAL = 4,
    RESOURCE_OVERFLOW = 5,
    RESOURCE_LACK = 6,
    GAME_OVER = 100
}
```

### Parasites Invasion

This event is bound to the town.
Parasites eat products in the town. Products decrement is equal to parasites count in the event.
Number of parasites in one attack: [1..3].
Safe time (turns count) after attack: 5 * (parasites number in the last attack).

#### Example: MAP response message (for layer 1) with event "Parasites Invasion"

``` JSON
{
    "idx": 1,
    "posts": [
        {
        "type": 1,
        "name": "Minsk",
        "events": [
            {
                "parasites_power": 3,
                "tick": 111,
                "type": 3
            }
        ],
        "product": 29,
        "product_capacity": 200,
        ...
        },
        ...
    ],
    ...
}
```

* **parasites_power** - count of parasites
* **tick** - game's turn number
* **type** - event's type

### Bandits Attack

This event is bound to the town.
Bandits destroy armor in the town. Armor decrement is equal to bandits count in the event.
If amount of armor in the town is less then bandits count, than population of this town will be decreased!
Number of bandits in one attack: [1..3].
Safe time (turns count) after attack: 5 * (bandits number in the last attack).

#### Example: MAP response message (for layer 1) with event "Bandits Attack"

``` JSON
{
    "idx": 1,
    "posts": [
        {
        "type": 1,
        "name": "Minsk",
        "events": [
            {
                "hijackers_power": 2,
                "tick": 1,
                "type": 2
            }
        ],
        "product": 29,
        "product_capacity": 200,
        ...
        },
        ...
    ],
    ...
}
```

* **hijackers_power** - count of bandits
* **tick** - game's turn number
* **type** - event's type

### Arrival of Refugees

This event is bound to the town.
Refugees increase population of the town. Population increment is equal to refugees count in the event.
Number of refugees in one event: [1..3].
Safe time (turns count) after event: 5 * (refugees number in the last event).

#### Example: MAP response message (for layer 1) with event "Arrival of Refugees"

``` JSON
{
    "idx": 1,
    "posts": [
        {
        "type": 1,
        "name": "Minsk",
        "events": [
            {
                "refugees_number": 2,
                "tick": 1,
                "type": 4
            }
        ],
        "product": 29,
        "product_capacity": 200,
        ...
        },
        ...
    ],
    ...
}
```

* **refugees_number** - count of refugees
* **tick** - game's turn number
* **type** - event's type

### Train Crash

This event is bound to the train.
If two or more trains are on the same position/point and at the same time - this is the crash situation!
Crash can't happen in towns.
All trains which participated in a crash will be returned to it's town and all goods in trains will be thrown away.
Train can't be used after crash for some period of time (cooldown), this time (turns count) depends on town's level.

#### Example: MAP response message (for layer 1) with event "Train Crash"

``` JSON
{
    "idx": 1,
    "trains": [
        {
            "events": [
                {
                    "tick": 2,
                    "train": 2,
                    "type": 1
                }
            ],
            "cooldown": 2,
            "fuel": 400,
            "fuel_capacity": 400,
            "fuel_consumption": 1,
            "goods": 0,
            "goods_capacity": 40,
            "goods_type": null,
            ...
        },
        ...
    ],
    ...
}
```

* **train** - second participant of the crash
* **tick** - game's turn number
* **type** - event's type

### Upgrade

Player is able to upgrade his town or train(s). All upgrades are paid by armor.
To initiate upgrade client sends to server an UPGRADE action (this action is described above).

### Town upgrade

What does the town get as a result of upgrade? See in following table:

Level | Population Capacity | Product Capacity | Armor Capacity | Cooldown After Crash | Next Level Price
------|---------------------|------------------|----------------|----------------------|------------------
1 | 10 | 200 | 200 | 2 | 100
2 | 20 | 500 | 500 | 1 | 200
3 | 40 | 10000 | 10000 | 0 | None

Level 3 - is maximal town level.

### Train upgrade

What does the train get as a result of upgrade? See in following table:

Level | Goods Capacity | Fuel Capacity | Fuel Consumption | Next Level Price
------|----------------|---------------|------------------|------------------
1 | 40  | 400 | 1 | 40
2 | 80  | 800 | 1 | 80
3 | 160 | 1600 | 1 | None

Level 3 - is maximal train level.

### Rating

The server recalculates rating value (game score) on every turn for each player.
The rating can be found on MAP layer 1.

Calculation formula:

    RATING = <population> * 1000 + sum(<upgrade level cost>) * 2 + <town.product> + <town.armor>

Where:

    <population> - current population in player's town (the value is multiplied by 1000)
    
    sum(<upgrade level cost>) - sum of armor spent for all upgrades (train(s), town) (the value is multiplied by 2)
    
    <town.product> + <town.armor> - sum of current amount of armor and product in player's town
