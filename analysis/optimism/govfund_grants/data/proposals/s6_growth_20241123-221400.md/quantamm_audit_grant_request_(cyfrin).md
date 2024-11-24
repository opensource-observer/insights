# Ether.fi OP Mainnet LRT Grant

# Basic Information

- **Project Name:** QuantAMM Audit Grant Request (Cyfrin)
- **Project Url:** https://app.charmverse.io/op-grants/quantamm-audit-grant-request-cyfrin-9897619391373831

## Contact Info

- **Email:** QuantAMM
- **Telegram:** QuantAMM is building a decentralized asset management platform with advanced Automated Market Maker mechanisms designed to reduce slippage and enhance asset rebalancing efficiency.
- **X handle:** christian@quantamm.fi
- **Discord/Discourse/Community:** @cadeharr
- **Demo:** https://x.com/QuantAMMDeFi
- **Other:** https://www.quantamm.fi/

# Grant Request

- **OP request Locked:** 0
- **OP request for User Incentives:** 49600
- **L2 Recipient Address:** 
    - **:** https://github.com/bulkcade/QuantAMM-OP-Audit/tree/pool-quantamm
- **Please briefly explain how we will be able to confirm that the OP has been spent:** https://www.quantamm.fi/research, https://www.quantamm.fi/, https://docsend.com/view/s/tqzcibqxu4hwpvku

# Project Details

- **If this is a resubmission from a declined Application, please provide the link to the previous Application, and briefly explain the main areas of improvement. If not please write (N/A):** Why are they going to succeed? QuantAMM performs a new variety of decentralised asset management. For LPs the focus is not on harvesting trading fees, but instead on the smart continuous allocation over time of pool value over the pool’s basket of reserves, following a pool creators’ chosen asset management strategy. They do this entirely onchain, and rebalance by offering arbitrage opportunities. Why is what they are going to build novel or valuable to Optimism? They are building a new, and fundamentally positive-sum, primitive for DeFi that enables much better management of liquidity onchain. QuantAMM can offer the OP ecosystem powerful onchain hedge-fund-style asset management strategies, unlike index protocols that have failed to take off. QuantAMM’s dynamic weight pools are an ultra-efficient mechanism for rebalancing LPs’ holdings that have the effect of increasing volume. For example, simulations show that that a standard Balancer pool [BTC, ETH, DAI] of initial size $1M with 1% fees produces $7.2m of arbitrage volume per year, while a QuantAMM momentum pool with the same size and constituents produces $20.3m volume. With OP’s low block times, low-cost transactions and mature DeFi/DEX-agg/arbitrage ecosystem, QuantAMM can offer OP a new and powerful product in DeFi. The protocol is launching later this year—they are Balancer V3 launch partners ( https://medium.com/@QuantAMM/quantamm-x-balancer-v3-046af77ddc81). How is this project likely to bring and keep new builders to the Optimism ecosystem? In the OP ecosystem, low gas costs means one can run more computationally-intensive strategies onchain as smart contracts, and run strategies that refresh at a faster frequency. This means that in the OP ecosystem a really broad range of possible quantitative strategies make sense — things that are simply not economical on mainnet become trivial on Optimism. This means that pool creators (who choose and tune a pool’s strategy) will have a world of possible strategies at their feet on OP. What are some comparable projects? What differentiates this one? While there have been DeFi protocols that aim to do ‘asset management’ of some form or another, they tends to rely on off-chain components for the strategy to be run (either off-chain compute to calculate the new desired allocation [e.g. enzyme] or a DAO voting mechanic for how rebalancing is done [e.g. tokemak]). There are also index protocols that run simple strategies however they rebalance monthly or quarterly. QuantAMM goes further than all the above by developing ways to run powerful, battle-tested quantitative asset management strategies (eg momentum, channel following, and approaches from mean-variance portfolio theory) entirely onchain at minimal gas cost, thanks to the development of novel algorithms for extracting useful signal from noisy oracle values in an extremely efficient manner. This means the strategies can also run hourly or daily, drastically increasing responsiveness. Further, QuantAMM has done work on optimal arbitrage (https://arxiv.org/abs/2402.06731) and optimal rebalancing efficiency for rebalancing a strategy via being an AMM pool (https://arxiv.org/abs/2403.18737). Rebalancing via being a time-varying geometric mean market maker (G3M) pool is extremely efficient, and is very often substantially more efficient than going out to an external DEX/AMM to rebalance. In fact, modelling QuantAMM pools against a LVR-like baseline, rebalancing via being an AMM can even me more efficient than trading against a CEX (due to the fact that one pays fees to a CEX, while being an AMM means the LPs rebalance as a maker–see page 2 of the QuantAMM protocol litepaper at https://www.quantamm.fi/litepapers for more info). All these advances, some of which are highly technical (e.g. using AMMs as the rebalancing mechanism) and some of which are more easily digestible (LPs do not have to rely on trust as the strategies are instantiated as SCs), combine to make an appealing novel suite of products that have broad appeal. Will this project be fee-based or free to the end user? To align incentives for LPs and pool creators, uplift-only fees (benchmarked against the deposit’s value) will be taken on withdrawal from the pool. (QuantAMM will develop pools for initial launch.) QuantAMM pools are AMM pools, they do provide a market. During rebalancing QuantAMM pools offer slightly off-market prices, which means if traders want to trade in that given direction it is cheaper for them than standard AMMs. Will this project be open-source? Yes. Have you worked on projects similar to this one? Yes.
- **Do you have a code audit for your project?:** 1. What makes them well-positioned to accomplish your project goals? 2. Is this their first Web3 project? 3. If not, share links to their other projects (e.g., Github repository). 4. Have they worked on anything in the Optimism ecosystem?
- **Please briefly answer all project details questions:** If so, provide an estimate of how many months of funding runway this project has. If there is an active need for financial support, please outline.

# Market Analysis:

- **Please briefly answer all market analysis questions:** Please describe if so and any mitigation measures taken.

# Grant's impact

- **Please briefly answer all grant's impact questions:** No.
- **Full list of the project’s labeled contracts:** Scope: pool-quantamm Lines of Code: 3100 Audit type: Multi-phase Duration: Competition 5 weeks Based on Cyfrin and QuantAMM's conversation, we have decided the best security approach here is a multi-phase audit. This combines the expertise of the lead security researchers at Cyfrin, followed by a community competitive audit. Competitive Audit Phases for QuantAMM Phase 1: Cyfrin delivers NSLOC, Complexity, Start Date, Prize Pool Phase 2: A designated account manager will be assigned to onboard and support throughout the entire competition. The account manager will oversee and monitor the community, support the protocol and assist in the competition's marketing. Phase 3: Cyfrin’s marketing team will use its social channels and the Solodit community to attract auditors to the competition. Phase 4:A codebase will be live on the CodeHawks platform for a pre-agreed period of time. Once the time has elapsed, judging will take place. Phase 5: A judge will be assigned to review all submitted bugs and score them accordingly. Once judging has taken place, there will be an allocated dispute period. Phase 6: All contestant submissions are anonymous to ensure judging remains impartial. Auditors will attack the codebase with various tools, tests, and methodologies throughout the private and competitive audit. Cyfrin will support QuantAMM in the competitive audit process and mitigations, providing a final report of the audit competition.

# Metrics improved by OP incentives

- **Select the metric specified in the mission request:** Cyfrin
- **Fill out your metric objective:** N/A

# Budget and Plan

- **Please briefly answer all budget and plan questions:** Hi @ will-cyfrin ! Please provide the real L2 address in the field L2 Recipient Address ("OP Request Section"), as it is required for the Foundation Report (and later the Public Tracker). Feel free to tag me when you do so I can include the information.

# Optimism relationship

- **Please briefly answer all Optimism relationship questions:** Updated OP Locked was removed as QuantAMM will pay the platform fee with funding commitment. The prize pool size was also reduced. Demo included

# External Contributions:

- **Use of Grant-as-a-service provider:** N/A
- **Contributions from non-team members:** 0x16779885375D32e7327fAde91f91B5A722bB5Cf4

# Compliance and Policies

- **Confirm understanding of clawback and milestone requirements:** Critical
- **Confirmation of understanding grant policies:** Cycle 29
- **KYC information requirement:** Not Completed
- **Certification of legal compliance for token distribution:** Audits application

# Milestones

- **Critical milestones for project execution:**     - {'milestone_type': 'Audit and Special Mission reviewers', 'op_tokens_request': 'Council', 'cycle': 'N/A', 'completed': 'N/A', 'title': 'Cyfrin Audit Report', 'source_of_truth': 'N/A', 'op_amount': 'N/A', 'op_deployment_date': 'N/A', 'incentives_due_date': 'N/A'}
