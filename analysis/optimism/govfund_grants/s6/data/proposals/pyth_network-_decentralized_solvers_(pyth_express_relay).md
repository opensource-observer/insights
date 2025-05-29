# Pyth Network: Decentralized Solvers (Pyth Express Relay)

**Project URL:** [Link](https://app.charmverse.io/op-grants/pyth-network-decentralized-solvers-pyth-express-relay-7897124393686845)

**Create your profile, add projects, and apply for Grant.**

Pyth Network 

**Email:**

MattDeFi@protonmail.com 

**Telegram:**

MattLosq 

**X handle:**

PythNetwork 

**Discord/Discourse/Community:**

https://discord.com/invite/PythNetwork 

**Demo:**

Live Project - Pyth Express Relay ( https://www.pyth.network/express-relay) 

**Other:**

N/A 

**OP request Locked:**

0

**OP request for User Incentives:**

70000

**L2 Recipient Address:**

 0x6c7D7714F536Cbdb0b3B0FDDea2747d5C4B2668E 

**Please briefly explain how we will be able to confirm that the OP has been spent:**

if the OP is not in the wallet, it has been spent (additional reporting to be done on reporting pages, etc) 

**If this is a resubmission from a declined Application, please provide the link to the previous Application, and briefly explain the main areas of improvement. If not please write (N/A)**

N/A

**Do you have a code audit for your project?**

Yes, Pyth Express Relay has undergone code audits (https://github.com/pyth-network/per/tree/main/audit-reports)

**Please briefly answer all project details questions**

Pyth Express Relay is an innovative decentralized solver system designed to eliminate Miner Extractable Value, facilitate faster rollouts for new protocols, and aggregate valuable DeFi opportunities for searchers. It introduces isolated priority auctions that allow searchers to compete for priority in performing critical operations like liquidations, improving capital efficiency and reducing costs for DeFi protocols and users. The primary usecase is in supporting DeFi projects, like lending and Perps protocols, support increased capital efficiency and deeper liquidity liquidations through a solver network. Success potential: Pyth Network has a strong track record in providing oracle services, and Express Relay builds on this expertise. The system is already live on Mode (via Ionic) and is supported by a robust network of searchers and DeFi protocols, soon to include Synthetix on Base. This ability and clear value proposition to eliminate MEV and support projects in improving their UX, positions PER for success on Optimism. Further, with the Superchain interop coming, this solution will help to power complex crosschain applications on the edge of interoperability tech. We see the potential for borrow/lending aggregators, Perps protocols, and much more to utilize this technology to support their protocols. Mission alignment: This project directly aligns with the mission to bring decentralized solvers to Optimism. By introducing a new primitive that connects DeFi protocols with a network of established searchers, Express Relay will enhance the DeFi ecosystem on Optimism by improving capital efficiency, reducing costs, and supporting innovation. Novelty : Pyth Express Relay offers a unique approach to decentralized solving by introducing isolated off-chain priority auctions. This novel mechanism eliminates the extractive role of miners/validators in transaction ordering, directly addressing the MEV problem that has long been considered inevitable in DeFi. Will the project be open source? Yes - https://github.com/pyth-network/per/tree/main Free or fee-based for end users? Integration with PER is permissionless and free. Using ER generates value for protocols by reducing liquidation rewards paid to searchers. See below for a fee example. Ionic, a user of ER on Mode, has cut liquidation rewards by 60%, improving collateral sales from 90% (via liquidating on Mode DEXs) to an average of 96% of its value by using PER. This 60% improvement (from 90% to 96%) is distributed as follows: the protocol captures 70%, the winning searcher 26%, and the Pyth DAO 4%. Is it composable with other projects on Optimism? How? Yes, Pyth Express Relay is highly composable. It's designed to integrate with various DeFi protocols, including lending platforms, perpetual futures, and derivatives protocols. Any protocol can permissionlessly integrate with it - protocols can broadcast liquidations to PER where searchers will then bid during the auction period.

**Please briefly answer all market analysis questions**

Competitors and differentiation: While there are other MEV mitigation solutions, Express Relay differentiates itself by offering a comprehensive solution that not only reduces MEV but also accelerates protocol deployment and aggregates DeFi opportunities for searchers. Its existing integrations and proven track record on other chains give it a competitive edge. Other competitions, most notably CowSwap and 1inch Fusion, provide this technology integrated at the DEX Swapping level for users but do not focus on supporting protocols as their focus. Current user base and estimation method : Express Relay is currently deployed to Mode in collaboration with Ionic, but has active deployment plans with protocols comprising $1 billion in total locked value (TVL) across 11 blockchains. On Base, it's planned to be integrated with Synthetix. The user base includes both the protocols using Express Relay and the end-users of these protocols benefiting from improved efficiency.

**Please briefly answer all grant's impact questions**

Steps to increase user interaction: Expand integration with key DeFi protocols on Optimism, Base, and across the Superchain Conduct 1:1 reachouts for OP developers on integrating and leveraging Express Relay Publish regular performance reports showcasing efficiency gains and MEV reduction on OP vs utilizing existing liquidity pools and automated swaps. Target audience characteristics: DeFi protocols on OP requiring efficient liquidations and order execution Traders and liquidity providers seeking more efficient markets with reduced MEV Developers building new DeFi applications on Optimism and the Superchain User interaction with Optimism: Users will benefit from more efficient DeFi operations on Optimism, including faster and more cost-effective liquidations, improved order execution, and reduced slippage due to the introduction of searcher bidding. Competitors on Optimism: There's no direct competitor that integrate at the protocol level, though there are many within the DEX Space which compete - this includes 1inch Fusion, Oku, etc.

**Full list of the project’s labeled contracts:**

The Pyth Express Relay on Mode is available here: 0x5Cc070844E98F4ceC5f2fBE1592fB1ed73aB7b48 and the Opportunity Adapter Factory there: 0x59F78DE21a0b05d96Ae00c547BA951a3B905602f You can find more details about the Pyth Express Relay contracts in the documentation .

**Select the metric specified in the mission request**

(Intent 3 Growth) # of transactions emitting event logs

**Fill out your metric objective**

Increase the number of transactions processed through Express Relay on the Superchain, emitting event logs by 5x. 

**Please briefly answer all budget and plan questions**

Size of request and justification: We request 70,000 OP tokens, allocated as follows: 70,000 OP: Growth Incentives: Subsidy of the Solver Rewards, capped at 5% OR $250, whichever is lower. While we initially considered distributing OP to projects to integrate (via developmental builders rewards), we do not forsee this as a valuable usage, as we would much rather deliver rewards directly to end-users (via more competitive bids). Subsidizing these searchers would boost their activity, leading to even greater savings for the protocols & better pricing for end-users. Plan for accomplishing the project (roadmap): Month 1-2: Deploy to OPM and have solvers ready to bid on auctions Month 2-3: Ionic Integrates with Pyth Express Relay Month 3-5: Deploy to Base & Integrate with Synthetix (not being rewarded as part of the grant) OP tokens distribution (percentages and initiatives): 100% (70,000 OP): Growth Incentives (Subsidy of Solver Rewards) As per OP rules, 40% of these would be payable upfront, the additional 60% is payable upon milestone completion. We just want to confirm with the grants council re hitting first milestones so it’s payable and we can continue incentivizing solvers. Subsidy Cap: Based on the current price of OP tokens, we can support at least 400 liquidations by capping the subsidy at $250 per liquidation (or 5% of the liquidation value, whichever is lower). For example, if we support 400 liquidations at $100,000 each, this results in a total liquidation TVL of $40 million. Subsidy Rate: With the subsidy capped at $250 per liquidation, this translates to 0.25% of each $100,000 liquidation. Small-Value Liquidations: For smaller value liquidations, the subsidy rate will be higher, up to the $250 cap. This ensures proportionally higher support for smaller liquidations (e.g., a $5,000 liquidation would receive the full $250, representing a 5% subsidy). Token distribution timeline: Six month distribution timeline (3-6 months depending on integration and usage activities) Sustainability post-incentives: Express Relay generates value through improved efficiency in DeFi operations and the elimination of extractive MEV. The initial goal is to use these incentives to further incentivize solvers & generate increased activity by integrators for a set period. Once integrated protocols have an initial baseline activity, protocols and users have an ongoing incentive to continue to utilize this, due to the increases in efficiency during liquidations. Additional accountability info: N/A Incentives on OPM: This grant application references deploying PER to the Superchain and onboarding users on Base, Mode, etc. As per the Grant Council rules on rebates to OPM, all subsidies will be targetted to those integrating on OPM. All Superchain related references are meant as purely informational, though Pyth will still target Superchain users as we expect a higher impact from users like Synthetix on Base.

**Please briefly answer all Optimism relationship questions**

Problem solved for Optimism: Pyth Express Relay addresses the critical issue of ample liquidity for tokens during liquidations in the Optimism ecosystem, enhancing the efficiency and fairness of DeFi operations. It also provides a solution for faster protocol deployment and liquidity bootstrapping. This will be critical for OP & Superchain going forward, as we attempt to bootstrap protocols across multiple chains, but they will be hamstrung by a lack of liquidity to process liquidations. Take Synthetix as an example, their support for certain perps margin assets is hamstrung by the ability to liquidate these with deep onchain liquidity at the best price. By using PER, we allow solvers to submit bids and provide liquidity outside of the chain, allowing protocols to grow further than the liquidity present on an OP stack chain. Ionic, the leading money-market on Mode with over $200M in TVL, was the first and day-1 user of Express Relay on mainnet. The Ionic founder stated : “ the integration is simple and it makes our lending markets much safer as we can rely on searchers to provide the liquidity up front to seize the collateral. On top of this, including the benefits of reducing value extraction and improving economic efficiency of the markets makes this a P0 feature for us to add! ” Value proposition: By improving capital efficiency, and reducing costs for DeFi protocols, Express Relay significantly enhances the overall DeFi experience on Optimism. This improvement will attract more users, protocols, and liquidity to the network. Growth potential for Optimism: The implementation of Express Relay has the potential to significantly increase DeFi activity on Optimism by enabling more efficient, fair, and attractive financial products. It can position Optimism as a leading chain optimized for DeFi. Commitment to building on Optimism: Pyth Express Relay is already live on Mode, but is ready to expand to the OP Superchain. We are committed to long-term development on Optimism and the Superchain, and are eager to explore deployment on existing OP Superchains as well. Express Relay aims to be a key player in OP interoperability, powering cross-Superchain protocols with full support once the interopability code is fully live and we can support solvers with integrations here. Deployment status: PER is currently deployed on Mode, partnering with Ionic, but has active deployment plans to support Synthetix on Base

**Use of Grant-as-a-service provider:**

No 

**Contributions from non-team members:**

Matt will be the Point of Contact for this proposal. 

**Confirm understanding of clawback and milestone requirements:**

yes

**Confirmation of understanding grant policies:**

yes

**KYC information requirement:**

yes

**Certification of legal compliance for token distribution:**

yes

## Critical Milestones

- **Title:** Integration with Ionic on OPM Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** ; **Completed:** ; **OP deployment date:** ; **Incentives due date:** 
- **Title:** Informational (non-critical): Superchain Volume Milestone Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** ; **Completed:** ; **OP deployment date:** ; **Incentives due date:** 
- **Title:** Demonostration of Efficiency Improvements Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** ; **Completed:** ; **OP deployment date:** ; **Incentives due date:** 
- **Title:** Informational Milestones (non-Critical) Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** ; **Completed:** ; **OP deployment date:** ; **Incentives due date:** 
- **Title:** Distribution of OP to Solvers on OPM Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** ; **Completed:** ; **OP deployment date:** ; **Incentives due date:** 
- **Title:** Creation of Notion & Dune Tracking Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** ; **Completed:** ; **OP deployment date:** ; **Incentives due date:** 
