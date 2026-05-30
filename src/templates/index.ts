export const TEMPLATES: Record<string, string> = {
  default: `title: 我的文字模拟器
description: 一个简单的文字模拟器游戏

stats:
  hp:
    name: 生命值
    min: 0
    max: 100
    default: 100
  mana:
    name: 法力值
    min: 0
    max: 100
    default: 50
  strength:
    name: 力量
    min: 0
    max: 20
    default: 5
  intelligence:
    name: 智力
    min: 0
    max: 20
    default: 5

character_creation:
  total_points: 15
  assignable:
    - strength
    - intelligence

events:
  - id: start
    title: 冒险开始
    description: 你站在一个分岔路口，前方有两条路。左边通向幽暗的森林，右边通向巍峨的山脉。
    choices:
      - text: 进入森林
        next_event: forest
      - text: 攀登山脉
        condition:
          strength: 5
        next_event: mountain
  - id: forest
    title: 幽暗森林
    description: 森林中光线昏暗，你听到远处有野兽的咆哮声。
    choices:
      - text: 小心前进
        next_event: forest_deep
      - text: 原路返回
        next_event: start
  - id: forest_deep
    title: 森林深处
    description: 你发现了一座古老的遗迹，散发着神秘的光芒。
    choices:
      - text: 触碰光芒
        effects:
          mana: 20
          hp: -10
        next_event: ending_magic
      - text: 离开遗迹
        next_event: forest
  - id: mountain
    title: 巍峨山脉
    description: 山路崎岖，寒风凛冽。你在半山腰发现了一个山洞。
    choices:
      - text: 进入山洞
        next_event: cave
      - text: 继续攀登
        condition:
          hp: 50
        next_event: mountain_top
  - id: cave
    title: 隐秘山洞
    description: 洞中温暖干燥，角落里有一些古老的书籍。
    choices:
      - text: 阅读书籍
        effects:
          intelligence: 3
          mana: -10
        next_event: ending_knowledge
      - text: 离开山洞
        next_event: mountain
  - id: mountain_top
    title: 山顶之巅
    description: 你成功登顶！眼前是壮丽的景色，你感到无比自豪。
    choices:
      - text: 欣赏风景
        next_event: ending_glory

endings:
  - condition:
      mana: 60
    title: 魔法觉醒
    description: 你体内的魔力被唤醒，成为了一位强大的法师。
  - condition:
      intelligence: 10
    title: 知识之路
    description: 你掌握了远古的知识，成为了最睿智的学者。
  - condition:
      hp: 80
      strength: 8
    title: 荣耀之巅
    description: 你用勇气和力量征服了高山，成为了传奇冒险家。
  - default: true
    title: 平凡之路
    description: 你的冒险结束了，虽然没有什么惊天动地的成就，但旅途本身就是最好的收获。

`,
  cultivation: `title: 修仙之路
description: 你是一个初入修真界的凡人，踏上修仙之路，追求长生与大道。

stats:
  hp:
    name: 生命
    min: 0
    max: 500
    default: 100
  qi:
    name: 灵力
    min: 0
    max: 500
    default: 50
  realm:
    name: 境界
    min: 0
    max: 100
    default: 0
  talent:
    name: 天赋
    min: 0
    max: 20
    default: 5
  willpower:
    name: 意志
    min: 0
    max: 20
    default: 5

character_creation:
  total_points: 12
  assignable:
    - talent
    - willpower

events:
  - id: start
    title: 踏上仙途
    description: 你站在青云山脚下，前方是传说中的修仙宗门——青云宗。山门巍峨，灵气环绕。
    choices:
      - text: 叩拜山门，请求入门
        next_event: entrance_test
      - text: 寻访附近散修
        next_event: wanderer
  - id: entrance_test
    title: 入门试炼
    description: 青云宗长老设下入门试炼——穿越灵气迷阵。
    choices:
      - text: 以天赋感应灵气
        condition:
          talent: 8
        effects:
          realm: 10
        next_event: accepted
      - text: 以意志强行突破
        condition:
          willpower: 5
        effects:
          hp: -30
          realm: 5
        next_event: accepted_hurt
      - text: 放弃试炼
        next_event: wanderer
  - id: accepted
    title: 入门成功
    description: 你的天赋让长老们眼前一亮。你被授予内门弟子身份，获得一部基础功法。
    effects:
      qi: 30
    choices:
      - text: 闭关修炼功法
        effects:
          qi: 50
          realm: 15
        next_event: inner_disciple
      - text: 探索宗门秘境
        next_event: secret_realm
  - id: accepted_hurt
    title: 勉强通过
    description: 虽然受伤，但你的意志打动了长老。你被收为外门弟子。
    choices:
      - text: 养伤修炼
        effects:
          hp: 40
          qi: 20
        next_event: outer_disciple
      - text: 强撑身体去听道
        effects:
          hp: -20
          realm: 8
        next_event: outer_disciple
  - id: wanderer
    title: 散修之路
    description: 你遇到了一位游历四方的散修老者，他看你有缘，愿意指点你一二。
    choices:
      - text: 接受指点
        effects:
          qi: 30
          talent: 2
        next_event: hermit_training
      - text: 婉拒，独自修行
        next_event: solo_path
  - id: inner_disciple
    title: 内门修炼
    description: 你在内门勤奋修炼，修为突飞猛进。宗门大比即将开始。
    choices:
      - text: 参加宗门大比
        condition:
          realm: 30
        next_event: tournament
      - text: 继续闭关
        effects:
          realm: 20
          qi: 100
        next_event: ending_ascension
  - id: outer_disciple
    title: 外门磨砺
    description: 外门生活艰苦，但你也逐渐成长。你听闻后山有一处灵眼。
    choices:
      - text: 冒险前往灵眼
        effects:
          qi: 80
          hp: -40
        next_event: spirit_eye
      - text: 踏实修炼
        effects:
          realm: 15
        next_event: ending_humble
  - id: secret_realm
    title: 宗门秘境
    description: 秘境中危险与机遇并存，你发现了一株千年灵芝和守护妖兽。
    choices:
      - text: 挑战妖兽
        condition:
          qi: 80
        effects:
          qi: -60
          hp: -50
          realm: 25
        next_event: inner_disciple
      - text: 悄悄取走灵芝
        condition:
          talent: 10
        effects:
          qi: 100
        next_event: inner_disciple
      - text: 安全退回
        next_event: inner_disciple
  - id: hermit_training
    title: 隐者修炼
    description: 在老者的指导下，你的修为稳扎稳打。老者临别前留下一部秘籍。
    choices:
      - text: 研读秘籍
        effects:
          qi: 60
          realm: 20
        next_event: ending_hermit
      - text: 下山历练
        next_event: solo_path
  - id: solo_path
    title: 独自修行
    description: 你独自在山中修行，虽慢但根基扎实。一日天降异象。
    choices:
      - text: 前往异象处
        effects:
          qi: 50
        next_event: ending_wanderer
      - text: 继续修炼
        effects:
          realm: 20
        next_event: ending_humble
  - id: spirit_eye
    title: 灵眼奇遇
    description: 灵眼中浓郁的能量涌入你体内，改造着你的根骨。
    choices:
      - text: 全力吸收
        effects:
          qi: 100
          realm: 30
        next_event: ending_humble
      - text: 适可而止
        effects:
          qi: 50
          realm: 15
        next_event: ending_humble
  - id: tournament
    title: 宗门大比
    description: 你在宗门大比中一路过关斩将，最终站在决赛场上。
    choices:
      - text: 全力一击
        condition:
          qi: 150
        effects:
          realm: 30
        next_event: ending_champion
      - text: 以巧取胜
        condition:
          talent: 12
        effects:
          realm: 20
        next_event: ending_champion

endings:
  - condition:
      realm: 60
      qi: 200
    title: 飞升大道
    description: 你的修为突破桎梏，天降祥云，白日飞升！三界震惊，万仙来朝。
  - condition:
      talent: 12
      realm: 40
    title: 宗门天骄
    description: 你以惊世天赋击败无数对手，成为宗门第一人。青云宗在你的带领下走向辉煌。
  - condition:
      willpower: 10
      realm: 30
    title: 隐世真修
    description: 你选择了一条与众不同的道路，隐于山林，与天地同修。虽无名声，但道行深厚。
  - condition:
      hp: 100
      realm: 20
    title: 散修大师
    description: 你以散修之身游历天下，积累无数奇遇，终成一代传奇散修。
  - default: true
    title: 凡人之路
    description: 修真的道路漫长而艰辛。你虽然没有走得很远，但在修行中找到了属于自己的平静。

`,
  survival: `title: 末日求生
description: 核战后的废土世界，辐射、变异生物、资源匮乏。你能在这片废土上活下来吗？

stats:
  hp:
    name: 生命
    min: 0
    max: 100
    default: 100
  hunger:
    name: 饱腹度
    min: 0
    max: 100
    default: 80
  radiation:
    name: 辐射值
    min: 0
    max: 100
    default: 10
  strength:
    name: 力量
    min: 0
    max: 20
    default: 5
  scavenging:
    name: 搜寻
    min: 0
    max: 20
    default: 5

character_creation:
  total_points: 10
  assignable:
    - strength
    - scavenging

events:
  - id: start
    title: 避难所出口
    description: 地下避难所的食物已经耗尽，你不得不打开厚重的铁门，走向地面世界。阳光刺痛你的眼睛，废土的气息扑面而来。
    choices:
      - text: 前往远处的城市废墟
        next_event: city_ruins
      - text: 查看避难所附近的废弃加油站
        next_event: gas_station
      - text: 沿着公路前行
        next_event: highway
  - id: city_ruins
    title: 城市废墟
    description: 曾经繁华的城市现在只剩下断壁残垣。你听到废墟深处有窸窣声……
    choices:
      - text: 小心搜寻物资
        condition:
          scavenging: 5
        effects:
          hunger: 20
        next_event: raider_encounter
      - text: 远离声音来源
        next_event: highway
  - id: gas_station
    title: 废弃加油站
    description: 加油站的便利店还残留着一些未开封的罐头。但这里似乎也有其他人来过。
    choices:
      - text: 搜集食物
        effects:
          hunger: 30
          radiation: 10
        next_event: traveler_meet
      - text: 查看地下油库
        condition:
          strength: 8
        effects:
          radiation: 25
        next_event: fuel_cache
      - text: 标记位置后离开
        next_event: highway
  - id: highway
    title: 荒废公路
    description: 公路两旁是被风沙侵蚀的汽车残骸。远处有一个路标指向「庇护所营地」。
    choices:
      - text: 前往庇护所营地
        next_event: shelter_camp
      - text: 搜查路边车辆
        effects:
          hunger: 15
          scavenging: 2
        next_event: mutated_creature
      - text: 原路返回
        next_event: start
  - id: raider_encounter
    title: 遭遇掠夺者
    description: 一群掠夺者从废墟中冲出来，他们手持生锈的武器，目光贪婪。
    choices:
      - text: 正面迎战
        condition:
          strength: 10
        effects:
          hp: -40
          hunger: 10
        next_event: victory_loot
      - text: 交出物资求和
        effects:
          hunger: -30
        next_event: highway
      - text: 逃跑
        effects:
          hp: -10
        next_event: highway
  - id: victory_loot
    title: 劫后丰收
    description: 你击败了掠夺者，从他们的营地搜刮到了大量物资和一张地图。
    choices:
      - text: 按地图前往军事基地
        next_event: military_base
      - text: 回到避难所休整
        next_event: start
  - id: traveler_meet
    title: 旅人相遇
    description: 你遇到了一个独行的旅人，他似乎对这片废土了如指掌。
    choices:
      - text: 和他交换情报
        effects:
          scavenging: 3
        next_event: shelter_camp
      - text: 结伴同行
        effects:
          hunger: -10
        next_event: shelter_camp
  - id: fuel_cache
    title: 油库发现
    description: 地下油库中竟然还有大量未使用的燃料！但辐射值也很高。
    choices:
      - text: 尽可能取走燃料
        effects:
          radiation: 30
        next_event: ending_fuel_boss
      - text: 放弃高风险战利品
        next_event: gas_station
  - id: shelter_camp
    title: 庇护所营地
    description: 这是一个由幸存者建立的营地，有围墙、哨塔和交易市场。营地领袖正在招募寻找净水装置的志愿者。
    choices:
      - text: 接受任务
        next_event: water_plant
      - text: 在营地交易休息
        effects:
          hunger: 20
          hp: 20
        next_event: ending_camp_life
  - id: mutated_creature
    title: 变异生物
    description: 一只巨大的变异老鼠从车辆残骸中冲出，獠牙滴着绿色的毒液！
    choices:
      - text: 战斗！
        condition:
          strength: 8
        effects:
          hp: -30
          hunger: 15
        next_event: highway
      - text: 迅速逃跑
        effects:
          hp: -5
        next_event: highway
  - id: military_base
    title: 军事基地
    description: 废弃的军事基地大门半掩，里面似乎有发电机在运转的声音。
    choices:
      - text: 进入指挥中心
        next_event: ending_military
      - text: 搜查军械库
        condition:
          scavenging: 10
        effects:
          strength: 5
        next_event: ending_armed
  - id: water_plant
    title: 净水工厂
    description: 工厂被变异的藤蔓植物覆盖，但核心的净水装置似乎还能运转。你看到了一只巨大的变异植物守卫。
    choices:
      - text: 凭借力量摧毁守卫
        condition:
          strength: 12
        next_event: ending_water
      - text: 寻找绕过守卫的路径
        condition:
          scavenging: 8
        next_event: ending_water

endings:
  - condition:
      radiation: 70
    title: 辐射变异
    description: 过度的辐射暴露使你的身体开始变异。你逐渐失去人性，变成废土上又一个变异生物……
  - condition:
      hunger: 60
      hp: 60
      scavenging: 10
    title: 废土生存大师
    description: 你凭借过人的搜寻能力和生存意志，在废土上建立了自己的营地。你是这片废土上最后的希望。
  - condition:
      strength: 12
      hp: 70
    title: 废土霸主
    description: 强大的力量让你在废土上无人能敌。掠夺者闻风丧胆，幸存者视你为救世主。
  - condition:
      scavenging: 6
    title: 净水英雄
    description: 你成功启动了净水装置！营地有了清洁的水源，幸存者们为你立了一座雕像。
  - condition:
      strength: 6
    title: 军事力量
    description: 你发现了军事基地中保存完好的武器库和通讯设备。你向外界发出信号，希望尚存。
  - default: true
    title: 废土流浪者
    description: 你在废土上默默流浪，虽然没做出什么壮举，但也顽强地活着。明天又是新的一天。

`,
  fantasy: `title: 龙与地牢
description: 一个经典的奇幻冒险世界。地牢深处埋藏着古老的宝藏与可怕的怪物。

stats:
  hp:
    name: 生命值
    min: 0
    max: 100
    default: 100
  mana:
    name: 魔力
    min: 0
    max: 100
    default: 40
  strength:
    name: 力量
    min: 0
    max: 20
    default: 5
  dexterity:
    name: 敏捷
    min: 0
    max: 20
    default: 5
  wisdom:
    name: 智慧
    min: 0
    max: 20
    default: 5
  gold:
    name: 金币
    min: 0
    max: 9999
    default: 0

character_creation:
  total_points: 12
  assignable:
    - strength
    - dexterity
    - wisdom

events:
  - id: start
    title: 冒险者公会
    description: 你走进冒险者公会，布告栏上贴满了委托。一位老者正在招募探索远古地牢的队伍。
    choices:
      - text: 接受地牢探索委托
        next_event: dungeon_entrance
      - text: 先去酒馆收集情报
        next_event: tavern
      - text: 接一个简单的护送任务
        effects:
          gold: 50
          hp: -10
        next_event: tavern
  - id: tavern
    title: 喧闹的酒馆
    description: 吟游诗人在弹唱英雄传奇。吧台边有个独眼佣兵在低声谈论远古地牢的秘密。
    choices:
      - text: 请佣兵喝一杯，打听情报
        effects:
          gold: -20
          wisdom: 2
        next_event: dungeon_entrance
      - text: 直接前往地牢
        next_event: dungeon_entrance
  - id: dungeon_entrance
    title: 地牢入口
    description: 远古地牢的入口被藤蔓覆盖，石门上刻着古老的符文。空气中有股霉味和魔法的气息。
    choices:
      - text: 解读符文
        condition:
          wisdom: 8
        effects:
          mana: 30
        next_event: rune_passage
      - text: 推开石门进入
        condition:
          strength: 8
        next_event: main_hall
      - text: 寻找密道
        condition:
          dexterity: 8
        next_event: secret_passage
      - text: 原路返回
        next_event: start
  - id: rune_passage
    title: 符文走廊
    description: 你解读了符文，一扇隐藏的门缓缓打开。走廊尽头是一间充满魔法能量的密室。
    choices:
      - text: 触碰魔法水晶
        effects:
          mana: 50
          hp: -10
        next_event: main_hall
      - text: 小心绕过去
        next_event: main_hall
  - id: main_hall
    title: 地牢主厅
    description: 巨大的石柱撑起穹顶，中央有一个石棺，周围散落着金币和魔法卷轴。一只石像鬼从阴影中苏醒！
    choices:
      - text: 用魔法对抗石像鬼
        condition:
          mana: 50
        effects:
          mana: -40
          hp: -20
          gold: 100
        next_event: treasure_room
      - text: 用力量击碎石像鬼
        condition:
          strength: 10
        effects:
          hp: -30
          gold: 80
        next_event: treasure_room
      - text: 敏捷地抢夺宝物后逃跑
        condition:
          dexterity: 10
        effects:
          gold: 60
        next_event: lower_levels
      - text: 战略性撤退
        next_event: dungeon_entrance
  - id: secret_passage
    title: 秘密通道
    description: 狭窄的密道中充满了陷阱，但前方的光芒表明这里有珍贵的宝物。
    choices:
      - text: 拆除陷阱
        condition:
          dexterity: 10
        effects:
          gold: 200
          dexterity: 2
        next_event: lower_levels
      - text: 冒险冲过去
        effects:
          hp: -25
          gold: 100
        next_event: lower_levels
      - text: 返回地牢入口
        next_event: dungeon_entrance
  - id: treasure_room
    title: 藏宝室
    description: 石像鬼守护的宝物超出了你的想象！金币堆成小山，魔法武器挂满墙壁。
    choices:
      - text: 取走魔法武器
        effects:
          strength: 5
          mana: 30
          gold: 500
        next_event: ending_hero
      - text: 只取金币
        effects:
          gold: 1000
        next_event: ending_rich
  - id: lower_levels
    title: 地牢下层
    description: 蜿蜒的阶梯通向地牢更深处。远方传来低沉的龙吟声……这是一条活着的龙！
    choices:
      - text: 挑战巨龙
        condition:
          strength: 15
          hp: 60
        effects:
          hp: -50
          gold: 2000
        next_event: ending_dragonslayer
      - text: 用智慧与龙谈判
        condition:
          wisdom: 12
          mana: 60
        effects:
          gold: 1500
          wisdom: 5
        next_event: ending_dragon_friend
      - text: 悄悄撤退
        next_event: ending_rich

endings:
  - condition:
      gold: 1000
      strength: 12
    title: 屠龙勇士
    description: 你斩杀了远古巨龙！你的名字被吟游诗人传唱，王国为你立起了雕像。
  - condition:
      wisdom: 15
      gold: 500
    title: 龙之盟友
    description: 你的智慧打动了巨龙。你们达成协议，巨龙守护王国，你成为最伟大的贤者。
  - condition:
      gold: 500
    title: 富甲一方
    description: 你带着满满的金币回到地面，买下了城镇的城堡，过着奢华的生活。
  - condition:
      mana: 80
      wisdom: 10
    title: 大法师
    description: 地牢的魔法能量彻底释放了你的潜能。你成为了王国首席大法师。
  - default: true
    title: 冒险继续
    description: 地牢的探索到此为止，但冒险者的生活永无止境。收拾行囊，准备下一次冒险吧！
`,
};

export const TEMPLATE_NAMES: Record<string, string> = {
  default: "默认模板",
  cultivation: "修仙模拟器",
  survival: "末日求生",
  fantasy: "龙与地牢",
};

export const EXAMPLE_EVENT_MD = `# 示例事件

这是一个 **Markdown** 格式的事件描述文件。

你可以使用 Markdown 语法来美化事件文本：

- 使用列表
- **加粗文字**
- *斜体文字*

> 甚至可以引用文字

事件中可以包含丰富的描述内容。
`;
