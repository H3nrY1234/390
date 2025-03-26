import pygame
import sys
import random
from itertools import combinations
import os
# Initialize Pygame
pygame.init()

# Screen size
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Texas Hold'em - Multiplayer")

# Colors
green = (0, 128, 0)
white = (255, 255, 255)
black = (0, 0, 0)
light_gray = (200, 200, 200)
dark_gray = (50, 50, 50)
button_hover = (255, 215, 0)  # 金色

# 設定字體
font = pygame.font.Font(None, 48)
button_font = pygame.font.Font(None, 32)  # 調整按鈕字體大小以適應按鈕範圍

# 背景圖片
background_img = pygame.image.load("poker_background.jpg").convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))


# Font settings
font = pygame.font.Font(None, 36)

# Card size
CARD_WIDTH, CARD_HEIGHT = 60, 90

# Button setup
check_button = pygame.Rect(200, 500, 100, 50)
call_button = pygame.Rect(320, 500, 100, 50)
raise_button = pygame.Rect(440, 500, 100, 50)
fold_button = pygame.Rect(560, 500, 100, 50)
all_in_button = pygame.Rect(680, 500, 100, 50)
bet_input_box = pygame.Rect(440, 560, 100, 40)

bet_amount = ""
input_active = False
current_player_index = 0
current_bet = 0
pot = 0
game_stage = "Pre-flop"

music_muted = False
mute_button = pygame.Rect(WIDTH - 60, 20, 40, 40)  # 右上角 40x40



# Start Menu Buttons
start_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
exit_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)

button_width, button_height = 200, 50


def draw_button(rect, text, is_hover):
    """ 繪製圓角按鈕，確保文字置中 """
    color = button_hover if is_hover else white
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, black, rect, 3, border_radius=10)

    # 確保文字在按鈕內置中
    text_surface = button_font.render(text, True, black)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect.topleft)




# Load card images properly
def load_card_images():
    suits = ["clubs", "diamonds", "hearts", "spades"]
    values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]
    images = {}

    for suit in suits:
        for value in values:
            filename = f"{value}_of_{suit}.png"
            if os.path.exists(filename):
                img = pygame.image.load(filename)
                images[f"{value}_of_{suit}"] = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))


    try:
        global card_back_image
        card_back_image = pygame.image.load("backside.jpg")  # ✅ 檔案應放在相同目錄
        card_back_image = pygame.transform.scale(card_back_image, (CARD_WIDTH, CARD_HEIGHT))
        images["back"] = card_back_image  # ✅ 把背面卡牌加到 card_images
    except pygame.error:
        print("⚠️ Error: Missing 'backside.jpg'. Using default placeholder.")
        card_back_image = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))  # **備用灰色背景**
        card_back_image.fill((100, 100, 100))
        images["back"] = card_back_image

    return images



card_images = load_card_images()
print(f"✅ Loaded card images: {list(card_images.keys())}")  # Debugging: list loaded images


# Define Player class
class Player:
    def __init__(self, name, position, chips=1000, position_name=""):
        self.name = name
        self.chips = chips
        self.hand = []
        self.folded = False
        self.current_bet = 0
        self.position = position
        self.position_name = position_name
        self.has_acted = False  # ✅ 新增，追蹤玩家是否行動過


def create_players(player_names):
    global players
    positions = [
        (150, 500), (550, 500),  # Bottom (BTN, CO)
        (700, 350), (700, 200),  # Right (SB, BB)
        (550, 50), (300, 50),  # Top (UTG, MP1)
        (100, 200), (100, 350)  # Left (MP2, MP3)
    ]

    poker_positions = ["BTN", "CO", "SB", "BB", "UTG", "MP1", "MP2", "MP3"][:len(player_names)]
    players = [Player(name, positions[i], position_name=poker_positions[i]) for i, name in enumerate(player_names)]


def handle_betting(action):
    global current_bet, pot, current_player_index, bet_amount

    player = players[current_player_index]

    if action == "Raise":
        try:
            raise_amount = int(bet_amount)
            if raise_amount <= current_bet:

                return
            if raise_amount > player.chips:

                return

            raise_difference = raise_amount - player.current_bet
            player.chips -= raise_difference
            pot += raise_difference
            current_bet = raise_amount
            player.current_bet = raise_amount

            # ✅ Reset others' has_acted status
            for p in players:
                if not p.folded and p != player:
                    p.has_acted = False

            player.has_acted = True  # ✅ This player has acted
            next_player()

        except ValueError:

            return

    elif action == "Check":
        if player.current_bet < current_bet:
            return
        player.has_acted = True
        next_player()

    elif action == "Call":
        call_amount = current_bet - player.current_bet
        if player.chips >= call_amount:
            player.chips -= call_amount
            pot += call_amount
            player.current_bet += call_amount
        else:
            pot += player.chips
            player.current_bet += player.chips
            player.chips = 0
        player.has_acted = True
        next_player()

    elif action == "Fold":
        player.folded = True
        player.has_acted = True
        next_player()

    elif action == "All-In":
        pot += player.chips
        player.current_bet += player.chips
        player.chips = 0
        player.has_acted = True
        next_player()


def next_player():
    global current_player_index, game_stage

    active_players = [p for p in players if not p.folded and p.chips > 0]

    if len(active_players) == 1:

        end_game()
        return

    # 🔁 Move to next player who hasn't folded or busted
    for _ in range(len(players)):
        current_player_index = (current_player_index + 1) % len(players)
        current_player = players[current_player_index]
        if not current_player.folded and current_player.chips > 0 and not current_player.has_acted:
            break
    else:
        # ✅ Everyone has acted -> advance stage
        advance_game_stage()
        return

    # ✅ 如果下一位係 AI，延遲觸發 AI 行動（避免畫面卡住）
    current_player = players[current_player_index]
    if "AI_" in current_player.name:
        pygame.time.set_timer(pygame.USEREVENT, 500)


def ask_rebuy(player):
    rebuy_amount = 1000
    asking = True
    font_big = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 32)
    confirm_button = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 50, 120, 40)

    while asking:
        screen.blit(background_img, (0, 0))
        msg = font_big.render(f"{player.name} Rebuy", True, white)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 60))

        pygame.draw.rect(screen, white, confirm_button, border_radius=12)
        pygame.draw.rect(screen, black, confirm_button, 2, border_radius=12)
        txt = font_small.render("Rebuy", True, black)
        screen.blit(txt, (confirm_button.x + 20, confirm_button.y + 8))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_button.collidepoint(event.pos):
                    player.chips = rebuy_amount
                    asking = False



def advance_game_stage():
    global game_stage, community_cards, deck, current_bet, current_player_index

    if game_stage == "Pre-flop":
        game_stage = "Flop"
        community_cards.extend(deck.deal(3))
    elif game_stage == "Flop":
        game_stage = "Turn"
        community_cards.extend(deck.deal(1))
    elif game_stage == "Turn":
        game_stage = "River"
        community_cards.extend(deck.deal(1))
    elif game_stage == "River":
        end_game()
        return

    current_bet = 0
    current_player_index = 0

    for player in players:
        if not player.folded:
            player.has_acted = False
        player.current_bet = 0

    # ✅ 在新回合開始後立即觸發 AI 行動
    trigger_ai_if_needed()



def trigger_ai_if_needed():
    current_player = players[current_player_index]
    if "AI_" in current_player.name:
        pygame.time.set_timer(pygame.USEREVENT, 500)


def end_game():
    global running

    active_players = [p for p in players if not p.folded]

    if len(active_players) == 1:
        winner = active_players[0]
        winner.chips += pot
    else:
        best_hand_player = max(active_players, key=lambda p: evaluate_best_hand(p.hand + community_cards)[0:2])
        winner = best_hand_player
        winner.chips += pot

    show_winner_screen(winner.name)
    running = False



def hand_rank(hand):

    values = sorted([Card.value_map[card.value] for card in hand], reverse=True)
    suits = [card.suit for card in hand]

    is_flush = len(set(suits)) == 1  # **是否為同花**
    is_straight = values == list(range(values[0], values[0] - 5, -1))  # **是否為順子**

    value_counts = {v: values.count(v) for v in set(values)}

    if is_flush and is_straight and values[0] == 14:
        return (10, values)  # 皇家同花順
    if is_flush and is_straight:
        return (9, values)  # 同花順
    if 4 in value_counts.values():
        return (8, sorted(value_counts, key=lambda x: (value_counts[x], x), reverse=True))  # 四條
    if sorted(value_counts.values()) == [2, 3]:
        return (7, sorted(value_counts, key=lambda x: (value_counts[x], x), reverse=True))  # 葫蘆
    if is_flush:
        return (6, values)  # 同花
    if is_straight:
        return (5, values)  # 順子
    if 3 in value_counts.values():
        return (4, sorted(value_counts, key=lambda x: (value_counts[x], x), reverse=True))  # 三條
    if list(value_counts.values()).count(2) == 2:
        return (3, sorted(value_counts, key=lambda x: (value_counts[x], x), reverse=True))  # 兩對
    if 2 in value_counts.values():
        return (2, sorted(value_counts, key=lambda x: (value_counts[x], x), reverse=True))  # 一對
    return (1, values)  # 高牌


def evaluate_best_hand(cards):
    best_score = (0, [], [])  # 🔥 (rank, sorted_values, best_hand)

    for hand in combinations(cards, 5):
        score = hand_rank(hand)
        if score[0] > best_score[0] or (score[0] == best_score[0] and score[1] > best_score[1]):
            best_score = (score[0], score[1], hand)

    return best_score  # back to (rank, values, best_hand)


def draw_game_screen():
    screen.fill((34, 139, 34))  # background

    table_width = 480
    table_height = 180
    table_x = (WIDTH - table_width) // 2
    table_y = (HEIGHT - table_height) // 2 + 20

    # green
    pygame.draw.ellipse(screen, (0, 100, 0), (table_x, table_y, table_width, table_height))

    # white
    pygame.draw.ellipse(screen, (255, 255, 255), (table_x + 20, table_y + 20, table_width - 40, table_height - 40), 3)

    # player name size
    small_font = pygame.font.Font(None, 22)

    # position of sit
    seat_positions = [
        (WIDTH // 2 - 180, HEIGHT - 170),  # BTN
        (WIDTH // 2 + 120, HEIGHT - 170),  # CO
        (WIDTH - 160, HEIGHT // 2 + 50),   # SB
        (WIDTH - 160, HEIGHT // 2 - 80),   # BB
        (WIDTH // 2 + 120, 70),            # UTG
        (WIDTH // 2 - 180, 70),            # MP1
        (100, HEIGHT // 2 - 80),           # MP2
        (100, HEIGHT // 2 + 50)            # MP3
    ]

    seat_positions = seat_positions[:len(players)]

    for i, player in enumerate(players):
        x, y = seat_positions[i]

        # 👤 玩家名稱：置中顯示，貼住手牌上方 10~15px
        name_surface = small_font.render(f"{player.name} (${player.chips})", True, white)
        name_rect = name_surface.get_rect(center=(x + CARD_WIDTH, y - 15))
        screen.blit(name_surface, name_rect)

        # 🂠 顯示玩家手牌，間距更大，避免重疊
        for j, card in enumerate(player.hand):
            card_x = x + j * (CARD_WIDTH + 10)
            card_image = (
                card_back_image
                if i != current_player_index else card_images[f"{card.value}_of_{card.suit}".lower()]
            )
            screen.blit(card_image, (card_x, y))

    # location of com card
    for i in range(5):
        card_x = WIDTH // 2 - 150 + i * (CARD_WIDTH + 10)
        card_y = HEIGHT // 2 - 20
        if i < len(community_cards):
            card = community_cards[i]
            screen.blit(card_images[f"{card.value}_of_{card.suit}".lower()], (card_x, card_y))
        else:
            screen.blit(card_back_image, (card_x, card_y))

    # HUD
    hud_x, hud_y = 20, 20
    hud_surface = pygame.Surface((200, 60), pygame.SRCALPHA)
    hud_surface.fill((50, 50, 50, 200))  # 半透明背景
    screen.blit(hud_surface, (hud_x, hud_y))
    pygame.draw.rect(screen, white, (hud_x, hud_y, 200, 60), 2, border_radius=10)

    hud_text = [
        f"Pot: ${pot}  Bet: ${current_bet}",
        f"{players[current_player_index].name} [{game_stage}]"
    ]
    for i, line in enumerate(hud_text):
        line_surface = small_font.render(line, True, white)
        screen.blit(line_surface, (hud_x + 10, hud_y + 5 + i * 20))


    draw_buttons()
    pygame.display.flip()
    draw_mute_button()


def draw_buttons():

    buttons = [
        (check_button, "Check"),
        (call_button, "Call"),
        (raise_button, "Raise"),
        (fold_button, "Fold"),
        (all_in_button, "All-In")
    ]


    start_x = 150
    button_spacing = 110

    for i, (button, text) in enumerate(buttons):
        button.x = start_x + i * button_spacing
        button.y = HEIGHT - 60

        pygame.draw.rect(screen, white, button, border_radius=10)
        pygame.draw.rect(screen, black, button, 2, border_radius=10)

        text_surface = font.render(text, True, black)
        screen.blit(text_surface, (button.x + 15, button.y + 10))


    bet_input_box.x = WIDTH // 2 - 50
    bet_input_box.y = HEIGHT - 110
    bet_input_box.width = 100
    bet_input_box.height = 40

    pygame.draw.rect(screen, white, bet_input_box, border_radius=10)
    pygame.draw.rect(screen, black, bet_input_box, 2, border_radius=10)

    bet_text = font.render(bet_amount, True, black)
    screen.blit(bet_text, (bet_input_box.x + 10, bet_input_box.y + 10))

def draw_mute_button():
    global music_muted

    # green for play red for mute
    color = (200, 0, 0) if music_muted else (0, 180, 0)
    pygame.draw.rect(screen, color, mute_button, border_radius=10)
    pygame.draw.rect(screen, white, mute_button, 2, border_radius=10)


    icon = "🔇" if music_muted else "🔊"
    icon_surface = button_font.render(icon, True, white)
    icon_rect = icon_surface.get_rect(center=mute_button.center)
    screen.blit(icon_surface, icon_rect)



def handle_event(event):
    global input_active, bet_amount,music_muted

    if event.type == pygame.MOUSEBUTTONDOWN:
        if mute_button.collidepoint(event.pos):
            global music_muted
            music_muted = not music_muted
            if music_muted:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
            return

        if check_button.collidepoint(event.pos):
            handle_betting("Check")
        elif call_button.collidepoint(event.pos):
            handle_betting("Call")
        elif raise_button.collidepoint(event.pos):
            input_active = True
        elif fold_button.collidepoint(event.pos):
            handle_betting("Fold")
        elif all_in_button.collidepoint(event.pos):
            handle_betting("All-In")
        elif bet_input_box.collidepoint(event.pos):
            input_active = True
        else:
            input_active = False

    elif event.type == pygame.KEYDOWN and input_active:
        if event.key == pygame.K_RETURN:
            input_active = False  # 按 Enter 退出輸入模式
            if bet_amount.strip().isdigit():
                handle_betting("Raise")  # ✅ 確認 Raise 行為
            else:
                print("\u26a0\ufe0f 請輸入合法的 Raise 金額")
        elif event.key == pygame.K_BACKSPACE:
            bet_amount = bet_amount[:-1]  # 刪除最後一個數字
        elif event.unicode.isdigit():
            bet_amount += event.unicode  # 只允許輸入數字


def main_game_loop():
    global running
    running = True
    clock = pygame.time.Clock()

    # 🔁 Start of loop: check if first player is AI
    current_player = players[current_player_index]
    if "AI_" in current_player.name:
        pygame.time.set_timer(pygame.USEREVENT, 500)

    while running:
        draw_game_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.USEREVENT:
                pygame.time.set_timer(pygame.USEREVENT, 0)  # Stop timer
                current_player = players[current_player_index]
                if "AI_" in current_player.name:
                    ai_decision(current_player)

            else:
                handle_event(event)

        clock.tick(30)

    print("\U0001f0cf 本局結束，準備下一局...")



class Card:
    value_map = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                 "10": 10, "jack": 11, "queen": 12, "king": 13, "ace": 14}

    def __init__(self, value, suit):
        self.value = value
        self.suit = suit

class Deck:
    def __init__(self):
        self.cards = [Card(value, suit) for suit in ["clubs", "diamonds", "hearts", "spades"]
                      for value in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]]
        random.shuffle(self.cards)

    def deal(self, num):
        return [self.cards.pop() for _ in range(num)] if len(self.cards) >= num else []

community_cards = []


def assign_positions():
    poker_positions = ["BTN", "CO", "SB", "BB", "UTG", "MP1", "MP2", "MP3"]

    # 確保玩家數量符合撲克座位限制
    if len(players) > len(poker_positions):
        return

    for i, player in enumerate(players):
        player.position_name = poker_positions[i]

    for p in players:
        print(f"{p.name}: {p.position_name}")


def start_game(player_names):
    global deck, game_stage, current_bet, pot, community_cards, players

    create_players(player_names)

    while len([p for p in players if p.chips > 0]) > 1:
        deck = Deck()

        # 旋轉莊家
        players = players[1:] + [players[0]]
        assign_positions()

        # 發牌 & 重設狀態
        for player in players:
            player.hand = deck.deal(2)
            player.folded = False
            player.current_bet = 0

        game_stage = "Pre-flop"
        current_bet = 10
        pot = 0
        community_cards = []

        # 設置盲注
        small_blind = 5
        big_blind = 10
        sb_player = players[2]
        bb_player = players[3]

        sb_player.chips -= small_blind
        sb_player.current_bet = small_blind
        pot += small_blind

        bb_player.chips -= big_blind
        bb_player.current_bet = big_blind
        pot += big_blind

        # UTG 行動
        global current_player_index
        current_player_index = 4 % len(players)

        # 主回合
        main_game_loop()

        # === 🔁 遊戲完後檢查誰輸光籌碼並詢問是否 rebuy ===
        for player in players:
            if player.chips == 0:
                ask_rebuy(player)

    # 最終勝者
    winner = [p for p in players if p.chips > 0][0]



def show_winner_screen(winner_name):
    font_big = pygame.font.Font(None, 64)
    font_small = pygame.font.Font(None, 36)

    continue_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 50)

    while True:
        screen.blit(background_img, (0, 0))

        # 顯示獲勝者名稱
        text = font_big.render(f"{winner_name} winner!", True, white)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 50))

        # 顯示「繼續遊戲」按鈕
        mouse_pos = pygame.mouse.get_pos()
        is_hover = continue_button.collidepoint(mouse_pos)
        draw_button(continue_button, "continue", is_hover)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_button.collidepoint(event.pos):
                    return  # 離開這個畫面，繼續遊戲


def ask_player_count():
    player_count = ""  # input 6 - 8
    input_box = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 - 30, 150, 50)
    start_button = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 + 50, 150, 50)
    active = False
    font_large = pygame.font.Font(None, 50)
    font_medium = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 30)

    while True:
        screen.fill((34, 139, 34))  # ✅ 背景改為更柔和的綠色


        # ✅ 讓背景框變成 深綠色 + 透明（比背景略深一點）
        popup_surface = pygame.Surface((400, 250), pygame.SRCALPHA)
        popup_surface.fill((0, 120, 0, 180))  # 調整為更柔和的綠色
        screen.blit(popup_surface, (WIDTH // 2 - 200, HEIGHT // 2 - 125))


        # ✅ 顯示標題
        title_text = font_large.render("Number of Players", True, white)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 100))

        subtitle_text = font_small.render("(6 - 8 players)", True, white)
        screen.blit(subtitle_text, (WIDTH // 2 - subtitle_text.get_width() // 2, HEIGHT // 2 - 70))

        # ✅ 美化輸入框
        pygame.draw.rect(screen, white, input_box, border_radius=12)
        pygame.draw.rect(screen, black, input_box, 2, border_radius=12)

        # ✅ 顯示輸入內容
        txt_surface = font_large.render(player_count, True, black)
        screen.blit(txt_surface, (input_box.x + 50, input_box.y + 5))

        # ✅ 按鈕（Hover 效果）
        mouse_pos = pygame.mouse.get_pos()
        button_color = (255, 255, 255) if not start_button.collidepoint(mouse_pos) else (200, 200, 200)
        pygame.draw.rect(screen, button_color, start_button, border_radius=12)
        pygame.draw.rect(screen, black, start_button, 2, border_radius=12)

        # ✅ 顯示按鈕文字
        start_text = font_medium.render("Start", True, black)
        screen.blit(start_text, (start_button.x + 45, start_button.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = True
                else:
                    active = False

                # ✅ 按 Start 鍵
                if start_button.collidepoint(event.pos):
                    try:
                        num_players = int(player_count)
                        if 6 <= num_players <= 8:
                            return num_players
                    except ValueError:
                        player_count = "6"  # 重置輸入

            if event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    try:
                        num_players = int(player_count)
                        if 6 <= num_players <= 8:
                            return num_players
                    except ValueError:
                        player_count = "6"  # 重置輸入
                elif event.key == pygame.K_BACKSPACE:
                    player_count = player_count[:-1]
                elif event.unicode.isdigit() and len(player_count) < 1:
                    player_count = event.unicode  # 只允許 6、7、8




def get_player_names(num_players):
    player_names = []
    input_box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 50)
    active = False
    text = ""
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)
    confirm_button = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 + 70, 120, 45)

    while len(player_names) < num_players:
        screen.blit(background_img, (0, 0))  # ✅ Use background
        prompt = title_font.render(f"Enter name for Player {len(player_names) + 1} ({len(player_names)+1}/{num_players}):", True, white)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 - 100))

        # Draw input box
        box_color = light_gray if active else dark_gray
        pygame.draw.rect(screen, box_color, input_box, border_radius=10)
        pygame.draw.rect(screen, white, input_box, 2, border_radius=10)

        input_text = font.render(text, True, white)
        screen.blit(input_text, (input_box.x + 10, input_box.y + 10))

        # Draw confirm button
        mouse_pos = pygame.mouse.get_pos()
        is_hover = confirm_button.collidepoint(mouse_pos)
        draw_button(confirm_button, "Confirm", is_hover)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = True
                else:
                    active = False
                if confirm_button.collidepoint(event.pos):
                    if not text.strip():
                        text = f"Player_{len(player_names) + 1}"
                    player_names.append(text)
                    text = ""
            elif event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    if not text.strip():
                        text = f"Player_{len(player_names) + 1}"
                    player_names.append(text)
                    text = ""
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    if len(text) < 12:  # limit name length
                        text += event.unicode

    return player_names


def main_menu():
    """ 主選單畫面 """

    pygame.mixer.music.load("game_background.ogg")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)

    global music_muted

    running = True
    while running:
        screen.blit(background_img, (0, 0))
        title_text = font.render("Welcome to Texas Hold'em", True, white)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

        start_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - 50, button_width, button_height)
        exit_button = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 20, button_width, button_height)

        mouse_pos = pygame.mouse.get_pos()
        draw_button(start_button, "Start Game", start_button.collidepoint(mouse_pos))
        draw_button(exit_button, "Exit", exit_button.collidepoint(mouse_pos))
        draw_mute_button()  # ✅ 畫出靜音按鈕

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if mute_button.collidepoint(event.pos):  # ✅ 加返呢段！
                    music_muted = not music_muted
                    if music_muted:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                    continue  # ✅ 避免再執行 start/exit click

                if start_button.collidepoint(event.pos):
                    game_mode_menu()
                elif exit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()



def game_mode_menu():
    """ 遊戲模式選單 """
    running = True
    while running:
        screen.blit(background_img, (0, 0))

        title_text = font.render("Select Game Mode", True, white)
        screen.blit(title_text, (WIDTH // 2 - 150, HEIGHT // 4))

        multiplayer_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
        singleplayer_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)
        back_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50)

        mouse_pos = pygame.mouse.get_pos()
        draw_button(multiplayer_button, "Multiplayer", multiplayer_button.collidepoint(mouse_pos))
        draw_button(singleplayer_button, "Single Player (AI)", singleplayer_button.collidepoint(mouse_pos))
        draw_button(back_button, "Back", back_button.collidepoint(mouse_pos))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if multiplayer_button.collidepoint(event.pos):
                    num_players = ask_player_count()
                    player_names = get_player_names(num_players)
                    start_game(player_names)
                elif singleplayer_button.collidepoint(event.pos):
                    start_single_player()
                elif back_button.collidepoint(event.pos):
                    main_menu()

def get_next_player_after(index):
    """ 從 index 之後開始找下一位未棄牌且未破產的玩家 """
    for i in range(1, len(players)):
        next_index = (index + i) % len(players)
        p = players[next_index]
        if not p.folded and p.chips > 0:
            return next_index
    return index  # fallback，如果找唔到就原地

def start_single_player():
    global players, deck, game_stage, current_bet, pot, community_cards, current_player_index

    # 初始化玩家（一次性創建）
    players = [Player("You", (150, 500), position_name="BTN")]
    ai_names = ["AI_1", "AI_2", "AI_3", "AI_4", "AI_5"]
    for i, name in enumerate(ai_names):
        players.append(Player(name, (150 + i * 100, 100), position_name=f"AI_{i + 1}"))

    while len([p for p in players if p.chips > 0]) > 1:
        print("\n🎲 開始新的一局！\n")
        deck = Deck()

        # 👉 轉莊家（BTN）
        players = players[1:] + [players[0]]
        assign_positions()

        # 發牌 & 狀態初始化
        for player in players:
            player.hand = deck.deal(2)
            player.folded = False
            player.current_bet = 0

        game_stage = "Pre-flop"
        current_bet = 10
        pot = 0
        community_cards = []

        # 設置盲注
        small_blind = 5
        big_blind = 10
        sb_index = 2
        bb_index = 3

        players[sb_index].chips -= small_blind
        players[sb_index].current_bet = small_blind
        pot += small_blind

        players[bb_index].chips -= big_blind
        players[bb_index].current_bet = big_blind
        pot += big_blind

        # ✅ 設定首位行動者為 BB 後第一位有效玩家
        current_player_index = get_next_player_after(bb_index)

        main_game_loop()

        # 檢查輸光籌碼玩家
        for player in players:
            if player.chips == 0:
                ask_rebuy(player)

    # 最終勝者
    winner = [p for p in players if p.chips > 0][0]
    print(f"\n🏆 最終勝者：{winner.name}！\n")



def ai_decision(player):
    global bet_amount

    best_rank, best_values, _ = evaluate_best_hand(player.hand + community_cards)

    if best_rank >= 7:
        action = "All-In"

    elif best_rank >= 5:  # 同花或順子
        raise_amount = max(current_bet * 2, 10)
        bet_amount = str(int(raise_amount))
        action = "Raise"

    elif best_rank >= 3:  # 兩對或三條
        if random.random() > 0.3:
            action = "Call"
        else:
            raise_amount = max(int(current_bet * 1.5), current_bet + 10)
            bet_amount = str(raise_amount)
            action = "Raise"

    else:
        if current_bet == 0:
            action = "Check"
        else:
            action = "Fold" if random.random() > 0.5 else "Call"

    handle_betting(action)


main_menu()