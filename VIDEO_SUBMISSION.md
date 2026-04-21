# Video Submission Guide
## Record & Submit Your Demo

Create a compelling 2-3 minute demo video for the hackathon.

---

## 🎬 Video Requirements

- **Duration:** 2-3 minutes
- **Content:** Demo running, Arc explorer verification
- **Quality:** 1080p minimum
- **Format:** MP4, MOV, or WebM
- **Audio:** Clear narration explaining what's happening
- **Proof:** Show 50+ transactions on Arc

---

## 🎥 Step 1: Recording Setup

### Install OBS Studio (Free)

```bash
# macOS
brew install obs

# Windows
# Download from https://obsproject.com/download

# Linux
sudo apt install obs-studio
```

### Configure OBS

1. Open OBS
2. Create new scene
3. Add source: "Display Capture" or "Window Capture"
4. Capture terminal window showing demo output
5. Add source: Browser (Arc explorer)
6. Arrange 2 windows side-by-side
7. Test audio (built-in mic or headset)

---

## 📹 Step 2: Record Demo Video Script

Follow this script (2-3 minutes):

```
[0:00-0:15] INTRO
"Hi, I'm [Your Name]. This is the Agent-to-Agent Compute Marketplace 
for the Arc x Circle hackathon. I'm going to demonstrate the full 
marketplace with 50+ real transactions on Arc testnet."

[0:15-0:45] SETUP
"The system consists of:
- 2 autonomous consumer agents with $5 USDC each
- 3 autonomous provider agents offering compute services
- A FastAPI backend handling metering, pricing, and settlement
- A Vyper smart contract on Arc managing payments

Let's run the demo..."

[0:45-1:15] RUN DEMO
(Show console output)
"Starting marketplace simulation... [wait for output]
60 transactions executing... agent requests, backend processing, 
payments settling on Arc...
[Wait until demo shows results]"

[1:15-1:45] RESULTS
"Demo complete! Results show:
- 60 transactions (requirement: 50+) ✓
- $0.0001 per-action pricing ✓
- Traditional gas would cost $1-5, making this impossible
- Arc + Nanopayments make it viable"

[1:45-2:15] ARC EXPLORER VERIFICATION
(Switch to Arc explorer)
"Now let me show you this on Arc testnet explorer...
[Navigate to contract address]
We can see the PaymentSettled events for each transaction,
all recorded immutably on the blockchain."

[2:15-2:45] AUTONOMOUS AGENTS
"The key innovation is that both consumer and provider agents
make autonomous decisions:
- Consumers check balance before purchasing
- Providers decide what work to accept
- All payments are trustless through the smart contract
- Real-time settlement in USDC"

[2:45-3:00] CONCLUSION
"This demonstrates that the agentic economy is viable ONLY
with solutions like Circle Nanopayments and Arc's low gas costs.
Thank you!"
```

---

## 🎬 Step 3: Recording Checklist

Before recording:

- [ ] Backend running (`python -m backend.main`)
- [ ] Terminal window clean and ready
- [ ] Arc explorer open in browser
- [ ] OBS configured and tested
- [ ] Microphone working
- [ ] Script memorized or printed
- [ ] Demo script ready to run

Recording steps:

1. Start OBS recording
2. Read intro (0-15s)
3. Explain architecture (15-45s)
4. Run `python scripts/demo.py` (45-1:15)
5. Wait for completion, narrate results (1:15-1:45)
6. Switch to Arc explorer, show transactions (1:45-2:15)
7. Explain autonomy concept (2:15-2:45)
8. Conclude (2:45-3:00)
9. Stop recording

---

## 💾 Step 4: Post-Processing

### Edit with Shotcut (Free)

```bash
# Install
brew install shotcut  # macOS

# Edit in Shotcut
1. Open video in Shotcut
2. Trim to 2:30 - 2:45
3. Add title/subtitle if desired
4. Export as MP4 (H.264)
```

### Upload to Storage

```bash
# Option 1: YouTube
1. Upload video (private or unlisted)
2. Copy share link
3. Paste in submission

# Option 2: Loom (easiest for demos)
1. Go to https://loom.com
2. Paste video
3. Get shareable link

# Option 3: Google Drive
1. Upload MP4
2. Make shareable (view access)
3. Get link
```

---

## 📝 Step 5: Write Submission Content

### Create SUBMISSION_NOTES.md

```markdown
# Hackathon Submission

## Project
Agent-to-Agent Compute Marketplace

## Tracks
- 🤖 Agent-to-Agent Payment Loop
- 🧮 Usage-Based Compute Billing

## Key Metrics
- **Transactions:** 60 (requirement: 50+)
- **Pricing:** $0.0001/unit (requirement: ≤$0.01)
- **Economic viability:** Impossible with traditional gas, viable with Nanopayments

## Demo Video
[Link to YouTube/Loom/Drive]

## GitHub Repository
[Link to repo]

## What Makes This Stand Out

1. **Novel combination:** First to merge two tracks meaningfully
2. **Economic rigor:** Proves margin gap that justifies Nanopayments
3. **Autonomous agents:** Both consumer and provider make independent decisions
4. **Real settlement:** 50+ transactions on actual Arc testnet
5. **Full stack:** Smart contracts + backend + agents + demo

## Technical Stack

- **Smart Contract:** Vyper on Arc
- **Backend:** FastAPI (Python)
- **Agents:** Async autonomous agents with independent decision-making
- **Settlement:** Circle Nanopayments + Arc blockchain
- **Integration:** x402 payment standard

## Why This Fails Without Nanopayments

- Traditional EVM: $1-5 per transaction
- For $0.10 compute job: 10-50× loss on gas alone
- Agents cannot survive economically
- Autonomous agent marketplaces impossible

## Why This Works With Nanopayments

- Arc + Nanopayments: $0.00001 per transaction
- For $0.10 job: Profitable with ~80% margin
- Agents can afford per-action settlement
- Autonomous agent economy becomes viable

## Feedback for Circle/Arc
[See FEEDBACK_TEMPLATE.md]

## Next Steps
[What would take this to production]
```

---

## 📤 Step 6: Final Submission

### Checklist

- [ ] Demo video recorded (2-3 min)
- [ ] Video uploaded (YouTube/Loom/Drive)
- [ ] GitHub repo public
- [ ] All code committed and pushed
- [ ] README.md complete
- [ ] SUBMISSION_NOTES.md ready
- [ ] Detailed feedback written (500+ words)
- [ ] Screenshots in `screenshots/` folder
- [ ] All requirements documented

### Submit via Hackathon Portal

Fill out submission form with:

1. **Project Title**
   ```
   Agent-to-Agent Compute Marketplace:
   Trustless Autonomous Agent Commerce with Circle Nanopayments
   ```

2. **Description**
   ```
   A marketplace where autonomous AI agents buy and sell compute services,
   settling payments in real-time USDC on Arc. Demonstrates economic
   viability (50+ transactions, ≤$0.01/action) only made possible by
   Circle Nanopayments and Arc's low gas model.
   ```

3. **GitHub Link**
   ```
   https://github.com/[username]/agent-compute-marketplace
   ```

4. **Demo Video Link**
   ```
   https://youtu.be/[video-id] OR https://loom.com/...
   ```

5. **Tracks Selected**
   - 🤖 Agent-to-Agent Payment Loop
   - 🧮 Usage-Based Compute Billing

6. **Team Members**
   ```
   [Your Name]
   GitHub: [username]
   Email: [email]
   ```

7. **Detailed Description**
   - Copy from SUBMISSION_NOTES.md
   - Include economic analysis
   - Explain why traditional model fails

8. **Feedback Submission** ($500 USDC bonus)
   - Copy from FEEDBACK_TEMPLATE.md
   - >500 words
   - Detailed, actionable suggestions

---

## 🎁 Step 7: Bonus Feedback ($500)

Make sure feedback is detailed:

```markdown
# Circle Nanopayments Feedback

## What Worked Well
[Specific examples, 200+ words]
- Clear documentation on...
- Easy integration of...
- Stable testnet...

## Pain Points
[Specific obstacles, 200+ words]
- Rate limiting unclear
- No agent wallet factory
- Gas cost calculation opaque

## Ideas for Improvement
[3-5 concrete suggestions, 200+ words]
- Add Python SDK
- Provide wallet factory contract
- Improve documentation on...

## Adoption Blockers
[2-3 barriers to wider adoption, 100+ words]
- x402 standard not widely known
- Limited examples in docs
- Vendor lock-in concerns

## Overall Assessment
[50+ words]
```

---

## ✅ Completion Checklist

**Video & Submission:**
- [ ] Demo video recorded (2-3 min)
- [ ] Video uploaded and shareable
- [ ] GitHub repo public with all code
- [ ] README.md complete
- [ ] Screenshots captured
- [ ] Submission form filled out
- [ ] Detailed feedback written
- [ ] All links verified

**Technical:**
- [ ] 50+ transactions shown
- [ ] Arc explorer verification
- [ ] Autonomous agents demonstrated
- [ ] Pricing validated (≤$0.01)
- [ ] Economic analysis explained

**Content:**
- [ ] Clear narration throughout
- [ ] Problem statement evident
- [ ] Solution demonstrated
- [ ] Results quantified
- [ ] Next steps outlined

---

## 📊 Final Submission Checklist

Before hitting submit:

1. Watch demo video once → Does it flow? Is audio clear?
2. Visit GitHub repo → Can judge see all files?
3. Read submission → Is it compelling?
4. Check feedback → >500 words? Actionable?
5. Verify links → All working?
6. Test demo once more → Does it still run?

---

## 🎉 You're Done!

**Congratulations on building and submitting! 🏆**

Final summary:
- ✅ Smart contract deployed
- ✅ Backend running
- ✅ Agents autonomous
- ✅ 50+ transactions executed
- ✅ Economic viability proved
- ✅ Demo recorded
- ✅ Feedback submitted
- ✅ Ready for judging

---

## 📞 Quick Reference

**Demo Command:**
```bash
python scripts/demo.py
```

**Backend Start:**
```bash
python -m backend.main
```

**Check Arc:**
```bash
https://testnet.arc.io/address/[contract-address]
```

**GitHub:**
```bash
git push origin main
```

---

## 🎯 Success Criteria for Judges

Judges will look for:

1. **Innovation:** ✅ Novel combination of two tracks
2. **Rigor:** ✅ Economic analysis + margin proof
3. **Execution:** ✅ 50+ real Arc transactions
4. **Autonomy:** ✅ Agents make independent decisions
5. **Polish:** ✅ Clear demo, complete docs, good video
6. **Feedback:** ✅ Detailed, actionable suggestions

You've covered all of these! Good luck! 🚀
