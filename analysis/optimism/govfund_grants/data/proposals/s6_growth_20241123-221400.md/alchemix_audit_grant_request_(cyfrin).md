# Ether.fi OP Mainnet LRT Grant

# Basic Information

- **Project Name:** Alchemix Audit Grant Request (Cyfrin)
- **Project Url:** https://app.charmverse.io/op-grants/alchemix-audit-grant-request-cyfrin-5604150300660156

## Contact Info

- **Email:** Alchemix
- **Telegram:** Alchemix offers self-repaying loans and yield strategies. This project creates a simple-to-use yield strategy that can bring TVL and associated swap value to Optimism.
- **X handle:** ov3rkoalafied@gmail.com
- **Discord/Discourse/Community:** @Ov3rkoalafied
- **Demo:** https://x.com/Ov3rKoalafied
- **Other:** https://alchemix.fi/

# Grant Request

- **OP request Locked:** 1474
- **OP request for User Incentives:** 14741
- **L2 Recipient Address:** 
    - **:** https://github.com/degenRobot/alchemix-transmuter/tree/master
- **Please briefly explain how we will be able to confirm that the OP has been spent:** N/A

# Project Details

- **If this is a resubmission from a declined Application, please provide the link to the previous Application, and briefly explain the main areas of improvement. If not please write (N/A):** Why are they going to succeed? Alchemix has already proven its success as a DeFi protocol, having attracted over $47M in total value locked (TVL) within three years of operation. Its unique approach to loans—self-repaying through yield on collateral—addresses major concerns for DeFi users: liquidation risk and interest payments. This creates an attractive environment for users seeking long-term loans and has built a strong and loyal user base. Why is what they are going to build novel or valuable to Optimism? This new project introduces an ERC-4626 vault to automate the Alchemix Transmuter process, making it more accessible and efficient. By simplifying how users earn a yield on their synthetic assets, the project will likely attract more users and sticky TVL—assets that remain locked in the protocol for an extended period. Automating the Transmuter process will reduce complexity and encourage greater user participation, drawing more users to Optimism. Additionally, the increased activity surrounding Alchemix's synthetic asset pools will drive higher transaction volumes, generate more transaction fees, and contribute to Optimism's overall network growth. What are some comparable projects? What differentiates this one? MakerDAO and Aave are comparable projects to Alchemix but differ in key ways. Both projects allow users to borrow by locking up collateral to mint synthetic assets, but they require manual repayment, charge interest, and have liquidation risks. Alchemix, on the other hand, offers self-repaying loans, with the collateral’s yield automatically repaying the loan over time. Have you worked on projects similar to this one? Yes. Will this project be fee-based or free to the end user? Free. Will this project pay for any portion of the service? No. Will this project be open-source? Yes.
- **Do you have a code audit for your project?:** 1. What makes them well-positioned to accomplish your project goals? 2. Is this their first Web3 project? 3. If not, share links to their other projects (e.g., Github repository). 4. Have they worked on anything in the Optimism ecosystem?
- **Please briefly answer all project details questions:** If so, provide an estimate of how many months of funding runway this project has. If there is an active need for financial support, please outline.

# Market Analysis:

- **Please briefly answer all market analysis questions:** Please describe if so and any mitigation measures taken.

# Grant's impact

- **Please briefly answer all grant's impact questions:** No.
- **Full list of the project’s labeled contracts:** Scope: alchemix-transmuter and dependencies for Optimism deployment Main: src/StrategyOp.sol | nSLOC:79 src/periphery/StrategyAprOracle.sol | nSLOC:11 src/interfaces/ITransmuter.sol | nSLOC:14 src/interfaces/IStrategyInterface.sol | nSLOC:25 src/interfaces/IVelo.sol | nSLOC:16 src/interfaces/ITransmuterBuffer.sol | nSLOC:6 src/interfaces/IAlchemist.sol | nSLOC:18 src/interfaces/IWhitelist.sol | nSLOC:7 Dependencies lib\tokenized-strategy-periphery\src\AprOracle\AprOracleBase.sol | nSLOC:15 lib\tokenized-strategy-periphery\src\utils\Governance.sol | nSLOC:27 lib\tokenized-strategy\src\BaseStrategy.sol | nSLOC:123 lib\tokenized-strategy\src\interfaces\ITokenizedStrategy.sol | nSLOC:78 Total nSLOC: 419 Audit type: Competitive audit Duration: 1 week Based on Cyfrin and Alchemix's conversation, we have decided the best security approach is a competitive audit. Potential Attack Vectors Highlighted by Alchemix The primary risk for the alETH transmuter looper is in the execution of the swap from ETH to alETH, which has the potential to be exploited or result in high slippage. (operational/economic) Alchemix wants its systems to be resilient to future changes in sequencer behavior, ensuring they can handle any potential front running risks as the technology evolves. Competitive Audit Structure Phase 1: Cyfrin delivers nSLOC, Complexity, Start Date, Prize Pool Phase 2: A designated account manager will be assigned to onboard and support throughout the entire competition. The account manager will oversee and monitor the community, support the protocol and assist in the competition's marketing. Any issues detected by the static analyser LightChaser will be added to the known issues list and included in the final report. Phase 3: Cyfrin’s marketing team will use its social channels and the Solodit community to attract auditors to the competition. Phase 4: The codebase will be live on the CodeHawks platform for a pre-agreed period of time. Phase 5: Once the time has elapsed, judging will take place. A judge will be assigned to review all submitted bugs and score them accordingly. All contestant submissions are anonymous to ensure judging remains impartial. Phase 6: After judging, there will be an appeals period. During this period, the Alchemix team and contest participants can raise questions regarding the severity and validity of submissions. Phase 7: A final report will be delivered to the Alchemix team. Auditors will attack the codebase with various tools, tests, and methodologies throughout the private and competitive audit. After the private audit, Alchemix will receive a comprehensive report.

# Metrics improved by OP incentives

- **Select the metric specified in the mission request:** Cyfrin
- **Fill out your metric objective:** https://discord.com/invite/alchemix

# Budget and Plan

- **Please briefly answer all budget and plan questions:** Hi @ jess@cyfrin.io ! Please provide the real L2 address in the field L2 Recipient Address ("OP Request Section"), as it is required for the Foundation Report (and later the Public Tracker). Feel free to tag me when you do so I can include the information.

# Optimism relationship

- **Please briefly answer all Optimism relationship questions:** Hello, please modify the github link to point to the exact scope. Also please give more details about the scoped contracts (name, nsloc ...)

# External Contributions:

- **Use of Grant-as-a-service provider:** N/A
- **Contributions from non-team members:** 0x16779885375D32e7327fAde91f91B5A722bB5Cf4

# Compliance and Policies

- **Confirm understanding of clawback and milestone requirements:** Critical
- **Confirmation of understanding grant policies:** Cycle 29
- **KYC information requirement:** Not Completed
- **Certification of legal compliance for token distribution:** Audits application

# Milestones

- **Critical milestones for project execution:**     - {'milestone_type': 'Audit and Special Mission reviewers', 'op_tokens_request': 'Council', 'cycle': 'N/A', 'completed': 'N/A', 'title': 'Cyfrin Audit Report', 'source_of_truth': 'N/A', 'op_amount': 'N/A', 'op_deployment_date': 'Dec 2', 'incentives_due_date': 'N/A'}
