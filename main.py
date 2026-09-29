<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Lion Miner Mini App</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <link rel="stylesheet" href="style.css">
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>

  <!-- Top Header / Stats Bar -->
  <div class="top-bar">
    <div class="profile-card">
      <div class="avatar" id="lionAvatar">🦁</div>
      <div class="level-badge" id="playerLevelBadge">Lvl 1</div>
    </div>
    <div class="stats-card">
      <div class="stat-row">
        <span class="stat-icon">🪙</span>
        <span class="stat-val" id="totalBalance">100.0000</span>
        <span class="stat-unit">GRAM</span>
      </div>
      <div class="stat-row secondary">
        <span class="stat-icon">⚡</span>
        <span class="stat-val" id="dailyRate">+0.500 / dag</span>
      </div>
    </div>
  </div>

  <!-- Main Content Area -->
  <main class="main-container">
    
    <!-- TAB 1: HOME / MINING -->
    <section id="tab-home" class="tab-content active">
      
      <!-- Progress Wood Panel -->
      <div class="wood-panel">
        <div class="panel-header">
          <span id="lionStageTitle">Kleine Welp</span>
          <span id="levelPercentText">75%</span>
        </div>
        <div class="progress-outer">
          <div class="progress-inner" id="levelProgressBar" style="width: 75%;"></div>
        </div>
      </div>

      <!-- Mascot Character Display -->
      <div class="mascot-display">
        <div class="glow-effect"></div>
        <div class="mascot-character" id="mascotIcon">🦁</div>
        <div class="mining-floating-coins" id="floatingCoins"></div>
      </div>

      <!-- Mining Yield / Claim Box -->
      <div class="wood-panel claim-panel">
        <div class="yield-title">Mijnbouw Opbrengst</div>
        <div class="yield-amount" id="unclaimedYield">+0.0000 GRAM</div>
        <button class="btn-3d btn-green" id="btnClaim">
          <span>⚡ Claim Opbrengst</span>
        </button>
      </div>

    </section>

    <!-- TAB 2: SHOP / DEPOSIT -->
    <section id="tab-shop" class="tab-content">
      <div class="wood-panel">
        <h2>🛒 Welpen Winkel</h2>
        <p>Verhoog je niveau en mine sneller!</p>
        
        <div class="shop-item">
          <div class="shop-icon">🥩</div>
          <div class="shop-info">
            <strong>Malse Biefstuk</strong>
            <p>+0.2% Mining Rate</p>
          </div>
          <button class="btn-3d btn-blue" onclick="buyUpgrade('steak')">10 GRAM</button>
        </div>

        <div class="shop-item">
          <div class="shop-icon">👑</div>
          <div class="shop-info">
            <strong>Gouden Kroon</strong>
            <p>+0.5% Mining Rate</p>
          </div>
          <button class="btn-3d btn-blue" onclick="buyUpgrade('crown')">25 GRAM</button>
        </div>

        <hr class="wood-divider">

        <div class="deposit-box">
          <h3>💳 Saldo Storten (Deposit)</h3>
          <p>Stort TON of GRAM om je welp sneller te laten groeien.</p>
          <button class="btn-3d btn-green" onclick="openDepositModal()">Stort Nu</button>
        </div>
      </div>
    </section>

    <!-- TAB 3: TASKS -->
    <section id="tab-tasks" class="tab-content">
      <div class="wood-panel">
        <h2>📋 Dagelijkse Taken</h2>
        <p>Voltooi taken voor extra GRAM beloningen!</p>

        <div class="task-item">
          <div class="task-info">
            <strong>Volg ons Kanaal</strong>
            <span>+1.00 GRAM</span>
          </div>
          <button class="btn-3d btn-green" onclick="claimTask(1)">Start</button>
        </div>

        <div class="task-item">
          <div class="task-info">
            <strong>Nodig 3 Vrienden Uit</strong>
            <span>+3.00 GRAM</span>
          </div>
          <button class="btn-3d btn-green" onclick="claimTask(2)">Start</button>
        </div>
      </div>
    </section>

    <!-- TAB 4: FRIENDS -->
    <section id="tab-friends" class="tab-content">
      <div class="wood-panel">
        <h2>👥 Vrienden Uitnodigen</h2>
        <p>Ontvang 10% van alle opbrengsten van je vrienden!</p>
        
        <div class="ref-link-box">
          <input type="text" id="refLink" value="https://t.me/DailygramMiner_bot?start=ref" readonly>
          <button class="btn-3d btn-yellow" onclick="copyRefLink()">Kopiëren</button>
        </div>
      </div>
    </section>

  </main>

  <!-- Bottom Navigation Bar -->
  <nav class="bottom-nav">
    <button class="nav-item active" onclick="switchTab('home')">
      <span class="nav-icon">🦁</span>
      <span class="nav-label">Home</span>
    </button>
    <button class="nav-item" onclick="switchTab('shop')">
      <span class="nav-icon">🛒</span>
      <span class="nav-label">Shop</span>
    </button>
    <button class="nav-item" onclick="switchTab('tasks')">
      <span class="nav-icon">📋</span>
      <span class="nav-label">Tasks</span>
    </button>
    <button class="nav-item" onclick="switchTab('friends')">
      <span class="nav-icon">👥</span>
      <span class="nav-label">Vrienden</span>
    </button>
  </nav>

  <script src="script.js"></script>
</body>
</html>
