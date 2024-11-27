# QuantAMM Audit Grant Request (Cyfrin)

**Project URL:** [Link](https://app.charmverse.io/op-grants/quantamm-audit-grant-request-cyfrin-9897619391373831)

**Audit Service Provider:**

Cyfrin

**Project name:**

QuantAMM 

**What is this project about?**

QuantAMM is building a decentralized asset management platform with advanced Automated Market Maker mechanisms designed to reduce slippage and enhance asset rebalancing efficiency. 

**Project Contact Email:**

christian@quantamm.fi 

**Telegram**

@cadeharr 

**X handle:**

https://x.com/QuantAMMDeFi 

**Website:**

https://www.quantamm.fi/ 

**Github:**

https://github.com/bulkcade/QuantAMM-OP-Audit/tree/pool-quantamm 

**Demo:**

https://www.quantamm.fi/research, https://www.quantamm.fi/, https://docsend.com/view/s/tqzcibqxu4hwpvku 

**Discord/Discourse/Community:**



**Other:**



**OP request locked:**

0

**OP request for User incentives:**

49600

**L2 Recipient Address:**

 0x16779885375D32e7327fAde91f91B5A722bB5Cf4 

**Distribution plan:**

Locking tokens for a year as outlined in the Lock-Up rule guide.

**What is this project going to build?**

Why are they going to succeed? QuantAMM performs a new variety of decentralised asset management. For LPs the focus is not on harvesting trading fees, but instead on the smart continuous allocation over time of pool value over the pool’s basket of reserves, following a pool creators’ chosen asset management strategy. They do this entirely onchain, and rebalance by offering arbitrage opportunities. Why is what they are going to build novel or valuable to Optimism? They are building a new, and fundamentally positive-sum, primitive for DeFi that enables much better management of liquidity onchain. QuantAMM can offer the OP ecosystem powerful onchain hedge-fund-style asset management strategies, unlike index protocols that have failed to take off. QuantAMM’s dynamic weight pools are an ultra-efficient mechanism for rebalancing LPs’ holdings that have the effect of increasing volume. For example, simulations show that that a standard Balancer pool [BTC, ETH, DAI] of initial size $1M with 1% fees produces $7.2m of arbitrage volume per year, while a QuantAMM momentum pool with the same size and constituents produces $20.3m volume. With OP’s low block times, low-cost transactions and mature DeFi/DEX-agg/arbitrage ecosystem, QuantAMM can offer OP a new and powerful product in DeFi. The protocol is launching later this year—they are Balancer V3 launch partners ( https://medium.com/@QuantAMM/quantamm-x-balancer-v3-046af77ddc81). How is this project likely to bring and keep new builders to the Optimism ecosystem? In the OP ecosystem, low gas costs means one can run more computationally-intensive strategies onchain as smart contracts, and run strategies that refresh at a faster frequency. This means that in the OP ecosystem a really broad range of possible quantitative strategies make sense — things that are simply not economical on mainnet become trivial on Optimism. This means that pool creators (who choose and tune a pool’s strategy) will have a world of possible strategies at their feet on OP. What are some comparable projects? What differentiates this one? While there have been DeFi protocols that aim to do ‘asset management’ of some form or another, they tends to rely on off-chain components for the strategy to be run (either off-chain compute to calculate the new desired allocation [e.g. enzyme] or a DAO voting mechanic for how rebalancing is done [e.g. tokemak]). There are also index protocols that run simple strategies however they rebalance monthly or quarterly. QuantAMM goes further than all the above by developing ways to run powerful, battle-tested quantitative asset management strategies (eg momentum, channel following, and approaches from mean-variance portfolio theory) entirely onchain at minimal gas cost, thanks to the development of novel algorithms for extracting useful signal from noisy oracle values in an extremely efficient manner. This means the strategies can also run hourly or daily, drastically increasing responsiveness. Further, QuantAMM has done work on optimal arbitrage (https://arxiv.org/abs/2402.06731) and optimal rebalancing efficiency for rebalancing a strategy via being an AMM pool (https://arxiv.org/abs/2403.18737). Rebalancing via being a time-varying geometric mean market maker (G3M) pool is extremely efficient, and is very often substantially more efficient than going out to an external DEX/AMM to rebalance. In fact, modelling QuantAMM pools against a LVR-like baseline, rebalancing via being an AMM can even me more efficient than trading against a CEX (due to the fact that one pays fees to a CEX, while being an AMM means the LPs rebalance as a maker–see page 2 of the QuantAMM protocol litepaper at https://www.quantamm.fi/litepapers for more info). All these advances, some of which are highly technical (e.g. using AMMs as the rebalancing mechanism) and some of which are more easily digestible (LPs do not have to rely on trust as the strategies are instantiated as SCs), combine to make an appealing novel suite of products that have broad appeal. Will this project be fee-based or free to the end user? To align incentives for LPs and pool creators, uplift-only fees (benchmarked against the deposit’s value) will be taken on withdrawal from the pool. (QuantAMM will develop pools for initial launch.) QuantAMM pools are AMM pools, they do provide a market. During rebalancing QuantAMM pools offer slightly off-market prices, which means if traders want to trade in that given direction it is cheaper for them than standard AMMs. Will this project be open-source? Yes. Have you worked on projects similar to this one? Yes.

**Who are the founders? please cover:**

Matthew Willetts was previously a Research Fellow at UCL Computer Science, an AI consultant with clients including Ford and IDEO, and has a PhD in machine learning from Oxford. Matthew has co-authored numerous research papers on MEV, multi-token arbitrage, LVR and dynamic portfolio rebalancing using AMMs. Christian Harrington has over a decade of finance technology experience, starting at London Stock Exchange and the London Metal Exchange, notably being responsible for development of global precious metals pricing systems. Later at Man Group Christian was lead technical architect for central order management. Christian has participated in regulatory compliance panels and has been a strong advocate for DeFi use cases in institutions, especially asset management.

**Is this project funded?**

Yes, see the press release here: https://coinmarketcap.com/community/articles/661173b7235e8143734d5f75/. QuantAMM has raised 1.85m USD to date, including from Chainlink (which invests in <10% of BUILD projects), Longhash, Mako Global Trading (a TradFi house), 8VC (an institutional VC fund) and from Fernando Martinelli personally.

**Has this project been the subject of a security breach?**

N/A not yet live

**Do you anticipate any particular issues or complexity in providing services to this project?**

No.

**Please provide details from your due diligence on this project and audit scope (the due diligence must contain the complexity of the scope, test coverage, and test methodologies applied to the scope)**

Scope: pool-quantamm Lines of Code: 3100 Audit type: Multi-phase Duration: Competition 5 weeks Based on Cyfrin and QuantAMM's conversation, we have decided the best security approach here is a multi-phase audit. This combines the expertise of the lead security researchers at Cyfrin, followed by a community competitive audit. Competitive Audit Phases for QuantAMM Phase 1: Cyfrin delivers NSLOC, Complexity, Start Date, Prize Pool Phase 2: A designated account manager will be assigned to onboard and support throughout the entire competition. The account manager will oversee and monitor the community, support the protocol and assist in the competition's marketing. Phase 3: Cyfrin’s marketing team will use its social channels and the Solodit community to attract auditors to the competition. Phase 4:A codebase will be live on the CodeHawks platform for a pre-agreed period of time. Once the time has elapsed, judging will take place. Phase 5: A judge will be assigned to review all submitted bugs and score them accordingly. Once judging has taken place, there will be an allocated dispute period. Phase 6: All contestant submissions are anonymous to ensure judging remains impartial. Auditors will attack the codebase with various tools, tests, and methodologies throughout the private and competitive audit. Cyfrin will support QuantAMM in the competitive audit process and mitigations, providing a final report of the audit competition.

**Optimism alignment**

QuantAMM are pre-launch (they are launch partners for Balancer V3 which is going live in Q4). The SCs being submitted are for the OP deployment of QuantAMM.

**What does this audit unlock for the project?**

This audit allows QuantAMM to launch its product to the market safely and securely, having undergone extensive auditing. Plus, it will provide extensive support to Balancer on Optimism.

**Client contact point to confirm audit completion:**

Christian Harrington - Co-Founder
christian@quantamm.fi 

## Critical Milestones

- **Title:** Cyfrin Audit Report Open; **Source of truth:** ; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** Cycle 29; **Completed:** Not Completed; **OP deployment date:** ; **Incentives due date:** 
