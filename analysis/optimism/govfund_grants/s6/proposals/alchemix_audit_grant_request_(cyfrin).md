# Alchemix Audit Grant Request (Cyfrin)

**Project URL:** [Link](https://app.charmverse.io/op-grants/alchemix-audit-grant-request-cyfrin-5604150300660156)

**Audit Service Provider:**

Cyfrin

**Project name:**

Alchemix 

**What is this project about?**

Alchemix offers self-repaying loans and yield strategies. This project creates a simple-to-use yield strategy that can bring TVL and associated swap value to Optimism. 

**Project Contact Email:**

ov3rkoalafied@gmail.com 

**Telegram**

@Ov3rkoalafied 

**X handle:**

https://x.com/Ov3rKoalafied 

**Website:**

https://alchemix.fi/ 

**Github:**

https://github.com/degenRobot/alchemix-transmuter/tree/master 

**Demo:**



**Discord/Discourse/Community:**

https://discord.com/invite/alchemix 

**Other:**



**OP request locked:**

1474

**OP request for User incentives:**

14741

**L2 Recipient Address:**

 0x16779885375D32e7327fAde91f91B5A722bB5Cf4 

**Distribution plan:**

Locking tokens for a year as outlined in the Lock-Up rule guide.

**What is this project going to build?**

Why are they going to succeed? Alchemix has already proven its success as a DeFi protocol, having attracted over $47M in total value locked (TVL) within three years of operation. Its unique approach to loans—self-repaying through yield on collateral—addresses major concerns for DeFi users: liquidation risk and interest payments. This creates an attractive environment for users seeking long-term loans and has built a strong and loyal user base. Why is what they are going to build novel or valuable to Optimism? This new project introduces an ERC-4626 vault to automate the Alchemix Transmuter process, making it more accessible and efficient. By simplifying how users earn a yield on their synthetic assets, the project will likely attract more users and sticky TVL—assets that remain locked in the protocol for an extended period. Automating the Transmuter process will reduce complexity and encourage greater user participation, drawing more users to Optimism. Additionally, the increased activity surrounding Alchemix's synthetic asset pools will drive higher transaction volumes, generate more transaction fees, and contribute to Optimism's overall network growth. What are some comparable projects? What differentiates this one? MakerDAO and Aave are comparable projects to Alchemix but differ in key ways. Both projects allow users to borrow by locking up collateral to mint synthetic assets, but they require manual repayment, charge interest, and have liquidation risks. Alchemix, on the other hand, offers self-repaying loans, with the collateral’s yield automatically repaying the loan over time. Have you worked on projects similar to this one? Yes. Will this project be fee-based or free to the end user? Free. Will this project pay for any portion of the service? No. Will this project be open-source? Yes.

**Who are the founders? please cover:**

Scoopy Trooples Twitter: https://x.com/scupytrooples?lang=en Alchemix already has almost $7m TVL on Optimism.

**Is this project funded?**

Alchemix has not received external investment and is currently sustained by revenue generated from its operations, such as protocol fees.

**Has this project been the subject of a security breach?**

No, but the protocol has been impacted by a vulnerability of Curve's pools More information can be found here: https://alchemixfi.medium.com/curve-exploit-post-mortem-7142e78bc339

**Do you anticipate any particular issues or complexity in providing services to this project?**

No.

**Please provide details from your due diligence on this project and audit scope (the due diligence must contain the complexity of the scope, test coverage, and test methodologies applied to the scope)**

Scope: alchemix-transmuter and dependencies for Optimism deployment Main: src/StrategyOp.sol | nSLOC:79 src/periphery/StrategyAprOracle.sol | nSLOC:11 src/interfaces/ITransmuter.sol | nSLOC:14 src/interfaces/IStrategyInterface.sol | nSLOC:25 src/interfaces/IVelo.sol | nSLOC:16 src/interfaces/ITransmuterBuffer.sol | nSLOC:6 src/interfaces/IAlchemist.sol | nSLOC:18 src/interfaces/IWhitelist.sol | nSLOC:7 Dependencies lib\tokenized-strategy-periphery\src\AprOracle\AprOracleBase.sol | nSLOC:15 lib\tokenized-strategy-periphery\src\utils\Governance.sol | nSLOC:27 lib\tokenized-strategy\src\BaseStrategy.sol | nSLOC:123 lib\tokenized-strategy\src\interfaces\ITokenizedStrategy.sol | nSLOC:78 Total nSLOC: 419 Audit type: Competitive audit Duration: 1 week Based on Cyfrin and Alchemix's conversation, we have decided the best security approach is a competitive audit. Potential Attack Vectors Highlighted by Alchemix The primary risk for the alETH transmuter looper is in the execution of the swap from ETH to alETH, which has the potential to be exploited or result in high slippage. (operational/economic) Alchemix wants its systems to be resilient to future changes in sequencer behavior, ensuring they can handle any potential front running risks as the technology evolves. Competitive Audit Structure Phase 1: Cyfrin delivers nSLOC, Complexity, Start Date, Prize Pool Phase 2: A designated account manager will be assigned to onboard and support throughout the entire competition. The account manager will oversee and monitor the community, support the protocol and assist in the competition's marketing. Any issues detected by the static analyser LightChaser will be added to the known issues list and included in the final report. Phase 3: Cyfrin’s marketing team will use its social channels and the Solodit community to attract auditors to the competition. Phase 4: The codebase will be live on the CodeHawks platform for a pre-agreed period of time. Phase 5: Once the time has elapsed, judging will take place. A judge will be assigned to review all submitted bugs and score them accordingly. All contestant submissions are anonymous to ensure judging remains impartial. Phase 6: After judging, there will be an appeals period. During this period, the Alchemix team and contest participants can raise questions regarding the severity and validity of submissions. Phase 7: A final report will be delivered to the Alchemix team. Auditors will attack the codebase with various tools, tests, and methodologies throughout the private and competitive audit. After the private audit, Alchemix will receive a comprehensive report.

**Optimism alignment**

Ethereum - $39.88m TVL Optimism - $6.92m TVL Arbitrum - $686,649 TVL

**What does this audit unlock for the project?**

This audit supports Alchemix in launching their product to the market safely and securely, having undergone extensive auditing.

**Client contact point to confirm audit completion:**

Chief Operations Officer, Ov3rkoalafied
ov3rkoalafied@gmail.com 

## Critical Milestones

- **Title:** Cyfrin Audit Report Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** Cycle 29; **Completed:** Not Completed; **OP deployment date:** Dec 2; **Incentives due date:** 
