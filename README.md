
# Table of Contents

| Section |
|--------------------------------------|
| [Introduction](#introduction) |
| [Eternal Social: The Vision](#eternal-social-the-vision) |
| [Core Technologies](#core-technologies) |
| [Key Features](#key-features) |
| [System Architecture](#system-architecture) |
| [Tech Stack](#tech-stack) |
| [Deployment Guide](#deployment-guide) |
| [User Interface](#user-interface) |
| [References](#references) |
| [Demonstration](#demonstration) |



## 🎥 Demonstration Video  (Click on thumbnail/Pic) Please do read below before going through the video

<div align="center">
 <h1>♾️🌍  Eternal Social  💫♾️</h1>
  <a href="https://youtu.be/1eY18p3zJd4" target="_blank">
    <img src="https://img.youtube.com/vi/1eY18p3zJd4/maxresdefault.jpg" alt="Watch on YouTube" width="800">
  </a>
</div>



### **My Motivation**

In 12th grade during COVID, I was constantly exposed to news and social media, where misinformation and divisive narratives thrived. I noticed a surge in racist and hateful comments—baseless generalizations amplified by bots and external influences. Constructive criticism is necessary, but outright hostility only deepens divides.  

At the time, I found myself engaging in online discussions, defending my country out of a sense of responsibility. However, I later realized how much time and energy these interactions drained, and how social media algorithms failed to curb misinformation and hate speech. The relentless political debates and fear-mongering created confusion, pulling people into echo chambers and deepening ideological divides.  

So when you posted on LinkedIn about the need for empathy, it resonated deeply. It reignited a fire I didn’t even realize was there. In just seven days, using skills I had gained from previous projects, I built **Eternal Social**—a self-monitoring social media platform integrating **blockchain and AI** to counter online toxicity.  

As I matured, I realized that divisiveness wasn’t about truth at all—it was about serving hidden agendas. Even today, we witness riots sparked by fake news , countless lives shattered by deep fakes and social media remains a breeding ground for hate.

We often talk about ending racism, hate speech etc...we have the technology to do it...yet we dont. The end of racism starts from ending racism on social media, i feel like we have the tools, we have the money but we dont really have the will to end it. 

This revelation made me even more determined to create a space where empathy and transparency can win over hate and manipulation of facts. Though still a work in progress, I believe Eternal Social will pave the way for a safer, more compassionate digital future.

---

### **Introduction**
**Eternal Social** is a next-generation social media platform where **AI regulates user interactions**, and **blockchain ensures AI's accountability**. Unlike traditional moderation methods that rely on human intervention, Eternal Social leverages **decentralized AI moderation** to maintain transparency, fairness, and accuracy and accountability of the system. Which in turn reduces the need for manual intervention and would help social media platforms regulate themselves by autonomous systems.

<div align="center">
<img src="https://github.com/user-attachments/assets/8a3618ab-a9cd-4f11-885c-c36d1a92306a" alt="Eternal Social Logo" width="400">
</div>  

### **Goals**
We prioritize **free speech** while promoting **responsible online behavior**. Users earn **points for empathetic interactions** and lose points for **toxicity, racism, or spreading misinformation**—but neutral conversations remain unaffected, and no private data is collected.  

To counter disinformation, we use **deep learning models trained on custom datasets** for **deepfake detection**, and a **balanced news verification system** that cross-references **left-wing, right-wing, and Gemini AI web agent searches** before issuing a verdict. This ensures **truthful, unbiased information** reaches users.  

---

## 🤔 Why Should Social Media Integrate This❓❓  
### **Future of social media:**
The **future of social media moderation** will be entirely **AI-driven**, eliminating the need for human intervention in content monitoring. AI will autonomously handle:  
- **Reputation scoring** based on user behavior.  
- **Fake news detection** through AI-powered cross-referencing.  
- **Deepfake identification** using advanced deep learning models.  

## 🌐 **Why Blockchain? And Why This System?** 🌐⛓️ 

AI must be **held accountable**, which is why **blockchain integration** is essential. By recording moderation actions on an **immutable ledger**, Eternal Social ensures:  

- **Transparent AI decisions** – Once AI moderates content, its action is permanently recorded, preventing hidden censorship or biased alterations.  
- **Decentralized moderation** – Instead of relying on a single company’s rules, blockchain allows a distributed, tamper-proof record of moderation, reducing corporate or political influence.  
- **Preventing historical manipulation** – **People often dig up old posts to manipulate narratives or incite violence. Blockchain can timestamp and verify context, ensuring old content isn't misused.**  
- **Curbing fake engagements** – **Bots and paid accounts artificially amplify hate speech and misinformation. With blockchain, interactions can be verified, reducing manipulation.**  
- **Cost-efficient enforcement** – By replacing expensive manual moderation with AI-backed blockchain verification, social media companies can cut costs while improving trust.  
- **A safer online space** – Users can verify whether flagged content was genuinely harmful or if it was unjustly censored, restoring confidence in online discourse.  

Blockchain isn't just about decentralization—it’s about **preserving truth, ensuring transparency, and protecting users from digital manipulation.**

Eternal Social **redefines content moderation** by merging AI efficiency with blockchain security—creating a **scalable, fair, and self-regulating social ecosystem**.  

---

## 🚀 User Flow and System Architecture (Please do zoom in if you would like)


![anuj_ki](https://github.com/user-attachments/assets/30a5e642-7974-41eb-a003-d382b4d7ac19)

Drive Link to view image: https://drive.google.com/file/d/1yOxxysPSt3xuhcp4CZO6TUBaC6jaCeba/view?usp=sharing

---

### 📌 Core Features & Modules  

#### 🏆 **1) Reputation Updation**  
- Users are assigned **reputation scores** based on their online behavior.  
- Blockchain **immutably** stores reputation data to prevent tampering.  
- High-reputation users get **privileges**, while low-reputation users would face  restrictions and possibly a ban if it goes below a certain level.  

#### 🚫📰 **2) Fake News Prevention using LeftWing/RightWing Sources and AI agents**  
- AI **analyzes content credibility** using cross-referenced sources.  
- Blockchain ensures **verified news sources** are immutable.  
- Misinformation is flagged, and users are alerted before sharing.
 

#### 🎭 **3) Deep Fake Detection**  
- AI scans images/videos for **manipulated media** using Deep Learning models.   
 

#### 💬 **4) Empathy Mode**  
- Users can **enable Empathy Mode** to transform their messages into a more **positive and constructive tone**.  
- Whether it's **criticism, professional discussions, or personal conversations**, the goal is to **foster respectful communication** without restricting emotions.  
- Ensures that **everyone is treated with dignity**, promoting a **healthier online environment**.  
- **Completely optional**—users can choose when to activate it for empathetic interactions.   
---

## 🛠️ Tech Stack  

- **AI/ML:** PyTorch, Gemini Model
- **Blockchain:** Ethereum, Solidity, Smart Contracts  
- **Backend:** Python (FastAPI), Web3.py  
- **Frontend:** HTML, CSS, JS  
---

# **How to Deploy Eternal-Social**  

## **Part 1: Smart Contract Deployment**  
1. Open a terminal and navigate to the project folder:  
   ```sh
   cd Eternal-Social
   ```  
2. Install Truffle globally if not installed:  
   ```sh
   npm install -g truffle
   ```  
3. Initialize Truffle:  
   ```sh
   truffle init
   ```  
4. Compile the smart contracts:  
   ```sh
   truffle compile
   ```  
5. Start a Truffle development blockchain:  
   ```sh
   truffle develop
   ```  
6. Deploy the contracts:  
   ```sh
   migrate
   ```  
7. After migration, you will get a contract address. Copy this address.  
   ![Contract Address](https://github.com/user-attachments/assets/1ecaa0a6-4e4d-4151-bbf0-013215cf47b6)  
8. Open `app3.py` and replace `deployed_contract_address` with the new contract address.  
   - Use **Ctrl+F** to find `deployed_contract_address`.  
   ![Replace Contract Address](https://github.com/user-attachments/assets/fc989ef1-9963-4ca9-9121-a2f96bb376c9)  

---  
## Intermediate:
1. Get a gemini key https://ai.google.dev/gemini-api/docs/api-key
2. Ctrl + F and find GOOGLE_API_KEY in app3.py
   
--
## **Part 2: Running the Backend**  
1. Open another terminal and install dependencies:  
   ```sh
   pip install -r requirements.txt
   ```  
2. Ensure all required libraries are updated to the latest versions.  
3. Start the FastAPI server:  
   ```sh
   python -m uvicorn app3:app --reload
   ```  
4. Open your browser and go to:  
   ```
   http://127.0.0.1:8000/
   ```  
   - Open **two tabs** of this URL.  
   ![Server Running](https://github.com/user-attachments/assets/f182830c-e6a7-4a73-a310-b1ac188f2ac0)  

5. Enter the **wallet address** obtained from `truffle develop`.  
   ![Wallet Address](https://github.com/user-attachments/assets/ee31ff68-462a-4d5d-8424-14d7880924bf)  
6. Use two different wallet addresses for two clients/users and click **Connect**.
   ![Connect and Enjoy](https://github.com/user-attachments/assets/42414274-df18-4fc8-abd1-dd69c7bc0211)
7. Enjoy the decentralized experience! 🚀
     
   
 


## User Interface
<div align="center">
 
  <h2>1) Deep Fake</h2>
  <img src="https://github.com/user-attachments/assets/fb907228-d5a7-408e-b79a-0c8ac0c36235" alt="Deep Fake" width="600">

  <h2>2) Fake News</h2>
  <img src="https://github.com/user-attachments/assets/26dd7f9e-a586-46b2-aced-0a9a506100e6" alt=" Fake News" width="600">

  <h2>💙3) Empathy Mode</h2>
  <img src="https://github.com/user-attachments/assets/988ad078-ac78-4324-a66d-6b94e5f3ca98" alt="Toxicity" width="600">

  <h2>☣️4) Toxicity</h2>
  <img src="https://github.com/user-attachments/assets/0cac4163-83d7-4c3d-89ab-e7fa047c2a03" alt="Additional Feature" width="600">
</div>



## References(If you want to know more of how to use / deploy websockets and blockchain you could check the following articles out!
- https://www.geeksforgeeks.org/what-is-web-socket-and-how-it-is-different-from-the-http/
- https://medium.com/walmartglobaltech/leveraging-web-sockets-for-powering-chat-platforms-38a4629b9688
- https://www.geeksforgeeks.org/simple-chat-application-using-websockets-with-fastapi/
- https://www.geeksforgeeks.org/deploy-a-smart-contract-on-ethereum-with-python-truffle-and-web3py/

## Demonstration:  
- **YouTube Video:** [Demonstration](https://youtu.be/1eY18p3zJd4)
- **Testing**
- Etherium Wallet address1:0x424f87f4d1a8e8890d8b3CdECd20000ED21006E8
- Etherium Wallet address2: 0xA114B7448c51C1B84668D5B08C29E1c6cC4dB3E2
