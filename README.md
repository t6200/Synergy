# 🎯 Synergy Discord Bot

**The Ultimate All-in-One Discord Bot** - Moderation, Tickets V2 System, Economy, Logging, and More!

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://github.com/Rapptz/discord.py)
[![License](https://img.shields.io/badge/License-GNU-green.svg)](LICENSE)

**Total Commands: 75+** | **Persistent Views** | **Production Ready** | **Music Playback**

---

## 📋 Table of Contents

1. [Features Overview](#-features-overview)
2. [Quick Start](#-quick-start)
3. [Complete Command List](#-complete-command-list)
4. [Tickets V2 System](#-tickets-v2-system)
5. [Moderation System](#-moderation-system)
6. [Economy System](#-economy-system)
7. [Utility Commands](#-utility-commands)
8. [Configuration](#-configuration)
9. [Troubleshooting](#-troubleshooting)

---

## ✨ Features Overview

### 🔨 **Advanced Moderation** (15 commands)
- Comprehensive moderation suite with ban, kick, mute, warn
- Temporary bans with auto-unban
- Discord native timeout support
- Channel management (lock, unlock, slowmode, nuke)
- Member statistics and role hierarchy protection
- Full logging of all actions

### 🎫 **Tickets V2 System** (6 commands)
- **Category dropdown selection** - Just like the famous Tickets V2 bot!
- Custom questions per category (up to 5)
- Professional ticket numbering (`category-0001`)
- Close with reason system
- 1-5 star rating system via DM
- Staff claim system
- Auto-transcripts sent to log channel
- Blacklist abusive users
- Real-time statistics
- **Persistent buttons** - Work after bot restart!

### 💰 **Economy System** (10 commands)
- Daily rewards, work, and crime systems
- PvP features: Rob other users
- Gambling: Coinflip, Slots (up to x10 multiplier)
- Custom currency names
- Leaderboard system
- Full balance management

### 📊 **Logging System**
- Message edits and deletions
- Member joins and leaves
- Role and channel changes
- Voice channel activity
- All moderation actions
- Ticket actions with transcripts

### 🛠️ **Utility Commands** (10 commands)
- User and server information
- Role and emoji information
- Snipe deleted/edited messages
- Interactive polls
- Reminder system
- Bot invite link generator

### ⚙️ **Configuration** (4 commands)
- Easy setup wizard (`/setup`)
- Customizable footer text and icons
- Per-server settings
- View current configuration

### 🤖 **Auto-Moderation** (2 commands)
- Anti-spam protection with customizable actions
- Anti-raid detection and alerts
- Banned words filter with multiple actions
- Mention spam prevention
- Caps spam detection
- Link spam filtering
- Exempt roles from auto-mod
- Full logging of all actions

### 👋 **Welcome & Goodbye** (6 commands)
- Customizable welcome messages with embed builder
- Goodbye messages when members leave
- Variable support ({user}, {server}, {member_count})
- Custom embeds with colors and images
- Auto-role on join
- Test commands to preview messages

### 📈 **Leveling System** (5 commands)
- XP-based leveling system
- Customizable XP ranges (15-25 XP per message by default)
- Level-up announcements with role rewards
- Server leaderboard (`/xpleaderboard`)
- Customizable level-up messages
- Role rewards at specific levels
- Server-wide leaderboard
- Rank cards with progress bars
- Customizable XP cooldowns

### 🎭 **Reaction Roles** (3 commands)
- Self-assignable roles via reactions
- Custom embed builder for role panels
- Multiple panels per server
- Add/remove roles dynamically

### 🎵 **Music System** (11 commands)
- Play music from YouTube and other sources
- Queue management with multiple songs
- Volume control (0-100%)
- Pause, resume, skip functionality
- Loop current song or entire queue
- Now playing display with thumbnails
- High-quality audio streaming
- FFmpeg-based playback
- Automatic disconnect on inactivity
- Song search by name or URL
- Beautiful embed displays for all music actions
- Works with emojis and custom emojis

### 🎉 **Giveaways** (4 commands)
- Timed giveaways with automatic winners
- Customizable duration and winner count
- React to enter (🎉)
- End giveaways early
- Reroll winners
- List all active giveaways
- DM notifications to winners

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- Discord account with server admin permissions

### 2. Installation

```bash
# Clone or download this repository
# Navigate to the bot directory

# Install dependencies
pip install -r requirements.txt
```

### 3. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Go to "Bot" tab → Click "Add Bot"
4. Enable these intents:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
5. Copy the bot token

### 4. Configuration

Create a `.env` file in the bot directory:

```env
DISCORD_TOKEN=your_bot_token_here
APPLICATION_ID=your_application_id_here
```

### 5. Invite Bot to Server

1. Go to OAuth2 → URL Generator
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select permissions:
   - Administrator (or specific permissions listed below)
4. Copy and open the generated URL

**Required Permissions:**
```
- Manage Roles
- Manage Channels
- Kick Members
- Ban Members
- Moderate Members
- Manage Messages
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Use Slash Commands
- Connect (Voice)
- Speak (Voice)
- Use Voice Activity
```

### 6. Install FFmpeg (Required for Music)

**Windows:**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the files
3. Add FFmpeg to your system PATH
4. Verify installation: `ffmpeg -version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 7. Run the Bot

```bash
python main.py
```

**Expected output:**
```
[OK] Loaded extension: cogs.moderation
[OK] Loaded extension: cogs.economy
[OK] Loaded extension: cogs.tickets
[OK] Loaded extension: cogs.config
[OK] Loaded extension: cogs.logging
[OK] Loaded extension: cogs.utility
[SYNC] Syncing slash commands globally...
[OK] Successfully synced 45 slash command(s) globally
Logged in as Synergy Bot#1234
```

### 7. Initial Bot Setup

```
/setup log_channel:#logs
/ticketpanel
```

**Done!** Your bot is ready to use! 🎉

---

## 📝 Complete Command List

### 🔨 Moderation Commands (15)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/ban <user> [reason]` | Permanently ban a user | Ban Members |
| `/tempban <user> <duration> [reason]` | Temporarily ban (auto-unban) | Ban Members |
| `/kick <user> [reason]` | Kick a user | Kick Members |
| `/mute <user> [duration] [reason]` | Mute a user (temp/permanent) | Manage Roles |
| `/unmute <user>` | Unmute a user | Manage Roles |
| `/timeout <user> <duration> [reason]` | Discord native timeout | Moderate Members |
| `/warn <user> [reason]` | Issue a warning | Kick Members |
| `/warnings <user>` | View user's warnings | Kick Members |
| `/clearwarnings <user>` | Clear all warnings | Kick Members |
| `/purge <amount> [user]` | Delete messages (1-100) | Manage Messages |
| `/lock [channel]` | Lock a channel | Manage Channels |
| `/unlock [channel]` | Unlock a channel | Manage Channels |
| `/slowmode <seconds> [channel]` | Set slowmode (0-21600s) | Manage Channels |
| `/nuke [channel]` | Clone & delete channel | Manage Channels |
| `/membercount` | Server member statistics | None |

### 🤖 Auto-Moderation Commands (2)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/automod [enabled] [anti_spam] [anti_raid] [spam_action]` | Configure auto-moderation | Administrator |
| `/bannedwords <action> [word]` | Manage banned words list | Administrator |

### 💰 Economy Commands (10)

| Command | Description | Cooldown |
|---------|-------------|----------|
| `/balance [user]` | Check balance | None |
| `/daily` | Daily reward (100 coins) | 24 hours |
| `/work` | Work for money (50-150) | 1 hour |
| `/crime` | Risky crime (10-500) | 2 hours |
| `/pay <user> <amount>` | Send money | None |
| `/rob <user>` | Rob user (40% success) | None |
| `/coinflip <amount> <heads/tails>` | Bet on coinflip | None |
| `/slots <amount>` | Slot machine (up to x10) | None |
| `/leaderboard [page]` | Top richest users | None |
| `/setcurrency <name>` | Set custom currency | Admin |

### 🎫 Ticket Commands (6)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/ticketpanel [title] [description] [channel]` | Create panel with categories | Administrator |
| `/adduser <user>` | Add user to ticket | Manage Channels |
| `/close [reason]` | Close ticket with reason | Manage Channels |
| `/transcript` | Generate transcript | Manage Channels |
| `/ticketblacklist <user> [remove]` | Blacklist/unblacklist user | Manage Guild |
| `/ticketstats` | View ticket statistics | None |

### 👋 Welcome/Goodbye Commands (6)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/welcomesetup [enabled] [channel] [autorole]` | Setup welcome messages | Administrator |
| `/welcomeembed` | Customize welcome embed | Administrator |
| `/goodbyesetup [enabled] [channel]` | Setup goodbye messages | Administrator |
| `/goodbyeembed` | Customize goodbye embed | Administrator |
| `/testwelcome` | Test welcome message | Administrator |
| `/testgoodbye` | Test goodbye message | Administrator |

### 📈 Leveling Commands (5)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/rank [user]` | View rank and XP | None |
| `/leaderboard [page]` | View XP leaderboard | None |
| `/levelconfig [enabled] [xp_min] [xp_max]` | Configure leveling | Administrator |
| `/levelrole <level> [role]` | Set role rewards for levels | Administrator |
| `/setxp <user> <xp>` | Set user's XP | Administrator |

### 🎭 Reaction Roles Commands (3)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/reactionrolepanel` | Create reaction role panel | Manage Roles |
| `/reactionrole <action> <message_id> <emoji> [role]` | Add/remove reaction role | Manage Roles |
| `/reactionrolelist` | List all reaction role panels | Manage Roles |

### 🎉 Giveaway Commands (4)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/giveaway <duration> <winners> <prize> [channel]` | Start a giveaway | Manage Guild |
| `/gend <message_id>` | End giveaway early | Manage Guild |
| `/greroll <message_id>` | Reroll giveaway winners | Manage Guild |
| `/glist` | List active giveaways | None |

### 🛠️ Utility Commands (10)

| Command | Description |
|---------|-------------|
| `/userinfo [user]` | Detailed user information |
| `/serverinfo` | Server statistics |
| `/avatar [user]` | View user's avatar |
| `/roleinfo <role>` | Role information and permissions |
| `/emoji <emoji>` | Emoji information |
| `/snipe` | View last deleted message |
| `/editsnipe` | View last edited message |
| `/poll <question> <options...> [duration]` | Create interactive poll |
| `/remind <time> <reminder>` | Set a reminder (s/m/h/d) |
| `/invite` | Get bot invite link |

### ⚙️ Configuration Commands (4)

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/setup` | Configure bot settings | Administrator |
| `/config` | View current configuration | Manage Guild |
| `/setfooter [icon_url] [text]` | Customize embed footer | Administrator |
| `/help` | Show all commands | None |

---

## 🎫 Tickets V2 System

Your bot now has **complete feature parity** with the famous Tickets V2 bot!

### ✨ Key Features

#### 1. Category Dropdown Selection
Users select from a dropdown menu (just like Tickets V2):
- 🎫 Multiple categories per server
- 📝 Custom descriptions for each
- 🎨 Custom emojis and colors
- Up to 25 categories supported

#### 2. Custom Questions Per Category
Each category can have up to 5 custom questions:
- Short or long answer types
- Required or optional fields
- Custom placeholders
- Collect specific information

#### 3. Professional Ticket Numbering
- Format: `category-0001`, `category-0002`
- Auto-incrementing per server
- Easy to reference and track

#### 4. Close with Reason
Staff provide closure reasons:
- Modal popup asks for reason
- Or use `/close reason:Text`
- Reason shown in transcript
- Sent to ticket creator

#### 5. Rating System ⭐
Users rate their experience:
- 1-5 star rating via DM
- Sent after ticket closes
- Logged to log channel
- 5-minute timeout

#### 6. Claim System
Staff can claim tickets:
- Click "Claim" button
- Shows who claimed
- Prevents duplicate claims

#### 7. Transcript System
Full conversation history:
- Timestamped messages
- Auto-sent to log channel on close
- Can be manually generated
- Includes all ticket information

#### 8. Blacklist System
Ban abusive users:
- `/ticketblacklist @user`
- Remove with `remove:True`
- Persistent across restarts

#### 9. Statistics Dashboard
View metrics with `/ticketstats`:
- Total tickets created
- Open vs closed count
- Breakdown by category

#### 10. Persistent Views
Buttons work forever:
- Survive bot restarts
- No re-setup needed
- Professional experience

### 🎯 Setup Guide

#### Step 1: Configure Log Channel
```
/setup log_channel:#logs
```

#### Step 2: Create Ticket Panel
```
/ticketpanel
```

This creates a panel with 3 default categories:
- 💬 **General Support** - General inquiries
- 🐛 **Bug Report** - Report bugs or issues
- 📝 **Other** - Something else

#### Step 3: Customize Categories (Optional)

Edit `save_data.json` to add custom categories:

```json
"ticket_categories": [
  {
    "id": "support",
    "name": "General Support",
    "description": "Get help with anything",
    "emoji": "💬",
    "color": "#5865F2",
    "support_roles": [123456789],
    "ping_roles": [987654321],
    "category_id": 111222333,
    "welcome_message": "Thanks for contacting us!",
    "custom_questions": [
      {
        "question": "What is your issue?",
        "placeholder": "Describe your problem",
        "long_answer": true,
        "required": true
      },
      {
        "question": "Your email",
        "placeholder": "email@example.com",
        "long_answer": false,
        "required": false
      }
    ]
  }
]
```

### 📊 User Flow

```
1. User clicks panel
   ↓
2. Dropdown appears with categories
   ↓
3. User selects category (e.g., "Bug Report")
   ↓
4. Modal appears with custom questions
   ↓
5. User fills in questions
   ↓
6. Ticket created: bug-report-0001
   ↓
7. Welcome embed with controls
   ↓
8. Staff can: Close, Claim, Transcript
   ↓
9. On close: Transcript → Log channel
   ↓
10. User gets DM to rate (1-5 stars)
```

### 🎨 Example Panels

#### Support Panel
```
/ticketpanel title:"💬 General Support" description:"Need help? Click below!" channel:#support
```

#### Bug Reports
```
/ticketpanel title:"🐛 Bug Reports" description:"Found a bug? Report it here!" channel:#bugs
```

#### Applications
```
/ticketpanel title:"📋 Staff Applications" description:"Want to join our team?" channel:#apply
```

---

## 🔨 Moderation System

### Core Features
- **Role Hierarchy Protection** - Can't moderate users with higher roles
- **Automatic Logging** - All actions logged to configured channel
- **Case System** - Every action creates a case entry
- **Temporary Actions** - Auto-unban, auto-unmute after duration

### Command Examples

#### Temporary Ban
```
/tempban @user 7d Spamming
```
Auto-unbans after 7 days.

#### Timeout User
```
/timeout @user 60 Calm down
```
Discord native timeout for 60 minutes.

#### Purge Messages
```
/purge 50 @user
```
Deletes last 50 messages from specific user.

#### Nuke Channel
```
/nuke #spam
```
Clones and deletes channel (removes all messages).

### Logging Output

All actions logged to your configured channel:

```
🔨 Member Banned | Case #0123
User: @BadUser (ID: 123456789)
Moderator: @StaffMember
Reason: Spam
```

---

## 💰 Economy System

### Features
- Persistent balances across restarts
- Custom currency names per server
- Cooldown system prevents spam
- Risk/reward balance

### Earning Money

**Safe Methods:**
- `/daily` - 100 coins every 24 hours
- `/work` - 50-150 coins every hour

**Risky Methods:**
- `/crime` - 10-500 coins (70% success rate)
- `/rob @user` - Steal 10-30% (40% success rate)

### Gambling

**Coinflip:**
```
/coinflip 100 heads
```
Win: Get 100 coins
Lose: Lose 100 coins

**Slots:**
```
/slots 50
```
Multipliers:
- 💎💎💎 = x10 (Jackpot!)
- ⭐⭐⭐ = x5
- Any 3 match = x3
- Any 2 match = x1.5

### Custom Currency

```
/setcurrency name:Diamonds
```

All commands will now show "Diamonds" instead of "coins".

---

## 🛠️ Utility Commands

### User Information
```
/userinfo @user
```
Shows:
- Account creation date
- Server join date
- Roles
- Permissions
- Status

### Server Information
```
/serverinfo
```
Shows:
- Member count breakdown
- Channel counts
- Role count
- Boost level
- Server features

### Polls
```
/poll "Best color?" "Red" "Blue" "Green" duration:5
```
Creates interactive poll with reactions.

### Reminders
```
/remind 30m Take a break
```
Bot DMs you after 30 minutes.

### Snipe Commands
```
/snipe
```
Shows last deleted message in channel (cached for 5 minutes).

```
/editsnipe
```
Shows last edited message.

---

## 🤖 Auto-Moderation System

### Features
- **Anti-Spam Protection** - Detects message spam and takes action
- **Anti-Raid Protection** - Detects mass join attempts
- **Banned Words Filter** - Custom word blacklist
- **Mention Spam** - Limit mentions per message
- **Caps Spam** - Detect excessive caps
- **Link Spam** - Block unwanted links
- **Exempt Roles** - Exclude staff from auto-mod

### Setup

```
/automod enabled:True anti_spam:True anti_raid:True spam_action:mute
```

**Spam Actions:**
- `warn` - Warning message
- `mute` - Temporary mute
- `kick` - Kick from server
- `ban` - Permanent ban

### Banned Words

```
/bannedwords add word:badword
/bannedwords remove word:badword
/bannedwords list
```

### How It Works

**Anti-Spam:**
- Detects 5+ messages in 5 seconds (configurable)
- Deletes spam messages
- Takes configured action

**Anti-Raid:**
- Detects 5+ joins in 10 seconds
- Alerts staff in log channel
- Tracks for monitoring

**Banned Words:**
- Instantly deletes messages
- Takes configured action
- Case-insensitive matching

---

## 👋 Welcome & Goodbye System

### Features
- **Custom Embed Builder** - Build embeds in Discord
- **Variable Support** - Dynamic content
- **Auto-Role** - Give roles on join
- **Test Commands** - Preview before enabling

### Setup Welcome Messages

```
/welcomesetup enabled:True channel:#welcome autorole:@Member
/welcomeembed
```

**Embed Builder Fields:**
- Title (e.g., "Welcome to {server}!")
- Description (multi-line)
- Color (hex code #5865F2)
- Footer text
- Image URL (optional)

**Available Variables:**
- `{user}` - User mention
- `{username}` - Username
- `{server}` - Server name
- `{member_count}` - Member count
- `{user_id}` - User ID

### Setup Goodbye Messages

```
/goodbyesetup enabled:True channel:#goodbye
/goodbyeembed
```

### Examples

**Welcome Message:**
```
Title: Welcome to {server}! 👋
Description: Hey {user}! You are member #{member_count}
Thanks for joining us!
Color: #5865F2
```

**Goodbye Message:**
```
Title: Goodbye {username} 😢
Description: {user} has left the server.
We're now {member_count} members.
Color: #ED4245
```

---

## 📈 Leveling System

### Features
- **XP Per Message** - Earn XP by chatting
- **Level Roles** - Reward roles at levels
- **Leaderboard** - Server-wide rankings
- **Rank Cards** - Beautiful progress display
- **Customizable** - Adjust XP rates

### Setup

```
/levelconfig enabled:True xp_min:15 xp_max:25 announce_levelup:True
```

### Level Roles

```
/levelrole level:5 role:@Active
/levelrole level:10 role:@Dedicated
/levelrole level:25 role:@Veteran
/levelrole level:50 role:@Legend
```

### XP System

**How XP Works:**
- Random XP per message (15-25 by default)
- 60 second cooldown between XP gains
- Level = √(XP / 100)
- XP for next level = (level + 1)² × 100

**Level Examples:**
- Level 1: 100 XP
- Level 5: 2,500 XP
- Level 10: 10,000 XP
- Level 25: 62,500 XP
- Level 50: 250,000 XP

### View Rank

```
/rank
/rank @user
```

**Rank Card Shows:**
- Current level
- Server rank position
- XP progress bar
- Total messages sent

### Leaderboard

```
/leaderboard
/leaderboard page:2
```

Shows top users by XP with medals for top 3.

---

## 🎭 Reaction Roles System

### Features
- **Self-Assignable Roles** - Users pick their own roles
- **Custom Embeds** - Beautiful role panels
- **Multiple Panels** - Unlimited panels per server
- **Add/Remove Dynamically** - Update anytime

### Create Panel

```
/reactionrolepanel
```

**Embed Builder Fields:**
- Title (e.g., "Select Your Roles")
- Description
- Color
- Footer

### Add Roles

```
/reactionrole action:add message_id:123456789 emoji:🎮 role:@Gamer
/reactionrole action:add message_id:123456789 emoji:🎵 role:@Music
/reactionrole action:add message_id:123456789 emoji:📺 role:@Movies
```

### How It Works

1. Create panel with custom embed
2. Add role mappings to message
3. Bot adds reactions automatically
4. Users click reactions to get/remove roles
5. Works instantly and persists across restarts

### Example Use Cases

**Color Roles:**
```
🔴 @Red
🟢 @Green
🔵 @Blue
```

**Game Roles:**
```
🎮 @Minecraft
🎯 @Valorant
⚔️ @League
```

**Notification Roles:**
```
📢 @Announcements
🎉 @Events
📰 @News
```

---

## 🎉 Giveaway System

### Features
- **Timed Giveaways** - Automatic winner selection
- **Multiple Winners** - Pick as many as needed
- **React to Enter** - Easy participation
- **Reroll Winners** - Change winners if needed
- **Auto-Notifications** - DM winners

### Start Giveaway

```
/giveaway duration:1h winners:1 prize:"Discord Nitro" channel:#giveaways
```

**Duration Format:**
- `30s` - 30 seconds
- `5m` - 5 minutes
- `2h` - 2 hours
- `7d` - 7 days

### Giveaway Flow

1. Staff starts giveaway
2. Embed posted with details
3. Bot adds 🎉 reaction
4. Users react to enter
5. Timer counts down
6. Winners selected randomly
7. Winners announced and DMed

### Manage Giveaways

**End Early:**
```
/gend message_id:123456789
```

**Reroll Winners:**
```
/greroll message_id:123456789
```

**List Active:**
```
/glist
```

### Example Giveaway

```
🎉 GIVEAWAY 🎉

Prize: Discord Nitro (1 month)

React with 🎉 to enter!
Winners: 3
Ends: in 6 hours

Hosted by: @Staff

[20 participants entered]
```

---

## ⚙️ Configuration

### Setup Command

```
/setup 
  log_channel:#logs 
  ticket_category:Support 
  muted_role:@Muted 
  support_roles:123456789,987654321
```

**Parameters:**
- `log_channel` - Where bot logs go
- `ticket_category` - Category for tickets
- `muted_role` - Role for muting
- `support_roles` - Ticket support roles (comma-separated IDs)
- `mod_roles` - Moderator roles
- `admin_roles` - Administrator roles

### View Configuration

```
/config
```

Shows all current server settings.

### Custom Footer

```
/setfooter 
  icon_url:https://i.imgur.com/abc123.png 
  text:Powered by Example Server
```

Sets custom footer on all bot embeds.

---

## 🔍 Troubleshooting

### Commands Not Showing Up?

**Wait 1-2 minutes** after bot starts. Global slash commands take time to sync.

**Still not working?**
1. Check bot has `applications.commands` scope
2. Try in a different server
3. Check bot logs for sync errors
4. Reinvite bot with correct scopes

### Buttons Not Working?

**After bot restart:** Views are persistent and should work automatically.

**If still broken:**
1. Recreate the panel with `/ticketpanel`
2. Check bot has proper permissions
3. Verify bot is online

### Permission Errors?

Make sure bot role is:
1. Above roles it needs to manage
2. Has required permissions
3. Not trying to moderate server owner/higher roles

### File Permission Error?

On Windows, if you get file access errors:
- The bot automatically handles this now
- Files are cleaned up after a 0.5s delay
- No action needed

### Economy Not Working?

Make sure:
1. Bot has write access to `save_data.json`
2. File isn't corrupted (should be valid JSON)
3. Restart bot if issues persist

---

## 📁 File Structure

```
Synergy/
├── main.py                 # Core bot file
├── requirements.txt        # Python dependencies
├── .env                    # Bot token (create this)
├── save_data.json         # Guild data (auto-created)
├── tickets.json           # Ticket data (auto-created)
├── bot.log               # Application logs (auto-created)
├── cogs/
│   ├── moderation.py     # Moderation commands
│   ├── economy.py        # Economy commands
│   ├── tickets.py        # Ticket system (Tickets V2)
│   ├── config.py         # Configuration commands
│   ├── logging.py        # Event logging
│   ├── utility.py        # Utility commands
│   ├── automod.py        # Auto-moderation system
│   ├── welcome.py        # Welcome/goodbye messages
│   ├── leveling.py       # Leveling/XP system
│   ├── reactionroles.py  # Reaction roles system
│   └── giveaways.py      # Giveaway system
└── README.md              # This file!
```

---

## 🎯 Feature Comparison

| Feature | Tickets V2 | Synergy | MEE6 | Carl-bot |
|---------|------------|---------|------|----------|
| Ticket System | ✅ | ✅ | ❌ | ❌ |
| Category Dropdown | ✅ | ✅ | ❌ | ❌ |
| Custom Questions | ✅ | ✅ | ❌ | ❌ |
| Rating System | ✅ | ✅ | ❌ | ❌ |
| Moderation | Limited | ✅ 15 cmds | ✅ | ✅ |
| Economy | ❌ | ✅ 10 cmds | ✅ | ❌ |
| Logging | Limited | ✅ Full | ✅ | ✅ |
| Utility | Limited | ✅ 10 cmds | Limited | ✅ |
| Self-Hosted | ❌ | ✅ | ❌ | ❌ |
| Free | Limited | ✅ | Limited | Limited |
| Customizable | Limited | ✅ | ❌ | Limited |

**Result: Synergy is the most feature-complete!** 🏆

---

## 📊 Statistics

- **Total Commands:** 65 slash commands
- **Total Cogs:** 11 modules
- **Lines of Code:** 8000+
- **Persistent Views:** ✅ Yes
- **Production Ready:** ✅ Yes
- **Open Source:** ✅ Yes
- **Auto-Moderation:** ✅ Yes
- **Leveling System:** ✅ Yes
- **Reaction Roles:** ✅ Yes
- **Giveaways:** ✅ Yes

---

## 🚀 Recently Added Features

- [x] Auto-moderation (anti-spam, anti-raid)
- [x] Welcome/goodbye messages
- [x] Leveling/XP system
- [x] Reaction roles
- [x] Giveaways

## 🔮 Upcoming Features

- [ ] Music commands
- [ ] Custom commands system
- [ ] Starboard system
- [ ] Suggestions system
- [ ] Advanced analytics dashboard

---

## 📝 Notes

- All commands use slash commands (no prefix)
- Permissions checked automatically
- All data persists across restarts
- Comprehensive error handling
- User-friendly error messages
- Professional embed styling

---

## 🤝 Support

For help with the bot:
1. Check this README
2. Use `/help` in Discord
3. Check bot logs in `bot.log`
4. Contact server administrators

---

## 📜 License

This project is licensed under the MIT License.

---

## 🎉 Credits

**Created by:** t_6200

**Synergy Bot** - The Ultimate All-in-One Discord Bot

**Total: 65 commands** | **11 modules** | **Production Ready** ❌

---

**⭐ If you like this bot, consider giving it a star on GitHub!**
