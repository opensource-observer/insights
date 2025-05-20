# Clusters.xyz

**Project URL:** [Link](https://app.charmverse.io/op-grants/clusters-xyz-7959150966012731)

**Audit Service Provider:**

Spearbit/Cantina

**Project name:**

Clusters.xyz 

**What is this project about?**

Clusters is a universal name service where a user’s identity follows them no matter which chain or L2 they’re on. People don’t sign their name differently based on geography or language, so why should it be any different in crypto? 

**Project Contact Email:**

foobar@delegate.xyz 

**Telegram**

@foobar0x 

**X handle:**

https://x.com/clustersxyz 

**Website:**

https://clusters.xyz/ 

**Github:**

https://github.com/clustersxyz 

**Demo:**



**Discord/Discourse/Community:**



**Other:**



**OP request locked:**

0

**OP request for User incentives:**

35000

**L2 Recipient Address:**

 0xB6B9E9e56AB5a4AF927faa802ac93786352f3af9 

**Distribution plan:**

All liquid OP will be used to payout bugs/issues for the Clusters.xyz Cantina competition. OP tokens will be used towards the total prize pool and used for any admin/support costs in running the competition like paying for a judge to review and evaluate the results.

**What is this project going to build?**

1. Why are they going to succeed? Clusters is a universal name service solving two core problems: (1) squatting; (2) wallet bundling. Existing name services like ENS and Basenames are powerful solutions, but struggle from users having to re-sign up on every new Superchain chain they go to. We allow a user to assign multiple addresses from different chains to a core identity in a single place, removing confusing mental burdens from the users. We’re also rolling out an ecosystem bootstrapping tool that helps users get one-click gas on new chains they configure their cluster with. Why is what they are going to build novel or valuable to Optimism? Optimism’s growth comes heavily from Superchain expansion, dominant players like Base and Worldcoin and even Sony. Clusters is built from the ground up to provide a seamless universal experience across all OPStack chains, fighting fragmentation and improving interoperability. How is this project likely to bring and keep new builders to the Optimism ecosystem? Builders will appreciate working with an identity service that is not only easy to use, but isn’t fragmented across every ecosystem they wish to integrate. What are some comparable projects? What differentiates this one? Comparable projects like Basenames or SpaceID are powerful solutions, but they are stuck in the 1 user = 1 address = 1 chain paradigm, so Clusters aims to augment these protocols by handling address aggregation and cross-L2 interop. Will this project be fee-based or free to the end user? The project is primarily fee-based, although certain core features like wallet bundling will be made available free to the end user. Will this project pay for any portion of the service? Clusters may subsidize or incentive signups depending on how closely we’re working with the target ecosystem. Will this project be open-source? Yes, contracts will be both verified onchain and available in an opensource GitHub repo.

**Who are the founders? please cover:**

The founder/CEO is twitter.com/0xfoobar, a well-known developer and thought leader in the space with over 150,000 followers. He previously launched https://delegate.xyz, which secures over $500 million worth of assets in the NFT ecosystem, including a strong presence on the Superchain.

**Is this project funded?**

Yes, raised a previous seed round.

**Has this project been the subject of a security breach?**

No

**Do you anticipate any particular issues or complexity in providing services to this project?**

No

**Please provide details from your due diligence on this project and audit scope (the due diligence must contain the complexity of the scope, test coverage, and test methodologies applied to the scope)**

Audit Scope: will be open sourced codebase: https://github.com/clustersxyz/clusters Testing: Clusters has fuzzing and unit tests. They will have 100% test coverage by the audit. Overview of scope: Complexity: Cross chain name registry allowing association of multiple wallet addresses under a single name. Has mechanisms to prevent name squating, pretty interesting. Uses layerzero for cross-chain messaging. - namemanagerhub.sol - manages the name service function, bidding/buying/tranferring names, along with pricing and banking of them - endpoint.sol - handles cross-chain comms via LZ, send/receives messages between different networks - clustershub.sol - extends namemanagerHub and adds cluster-specific functions, so creation/verification/deletion of clustors, and addition/removal within them as well. - enurablesetlib.sol set operations for bytes32 values - pricingharberger.sol implements harberger tax pricing model for the name service - pricingflat.sol - alternate pricing model that uses flat rate instead of harberger tax model - basicUUPSImpl - proxy upgrade standard and everything else in /interfaces/ Given the nature of the codebase, in terms of nloc, complexity of code and skills required the best solution would be to leverage a Cantina security competition. This project will be fully open source and a Cantina competition will align with open source ethos of this project. Competition details: We can be flexible on how we can structure the competition in terms of rewards, Clusters is also looking to pay the rest of the total cost that is not covered by the OP subsidy. We would structure the competition with a rewards pot of with 32,051 OP with 16,025 OP for the administration, facilitation and judging feeof the competition. We are looking to be subsidised by the OP grant of 35,000 OP tokens to cover a portion of the total cost of 48,076 - Clusters.xyz will be able to pay the surplus amount (13,076 OP) of the total cost not covered by the OP Grant. We do not anticipate needing any extensions, but if we encounter anything that would indicate the need for extensions we will inform the client immediately. A fix review period at the end of the competition will be handled and picked from the top performers of the competition and this review period will be scoped based exactly on the fixes/remediations created as a separate engagement which we will notify OP security council on the associated cost.

**Optimism alignment**

We’ve supported registration of a Cluster via Optimism since day 1 of our beta rollout. We identified Optimism and the Superchain as the dominant L2 ecosystem, and wanted to make sure we had a tangible presence there.

**What does this audit unlock for the project?**

The audit both builds user confidence and developer confidence for Clusters to be a robust building block primitive across the Superchain. It will also identify further improvements and efficiencies to enhance the protocol itself.

**Client contact point to confirm audit completion:**

Contact Spearbit team 

## Critical Milestones

- **Title:** Audit Completion (report or written approval by Clusters Team) Open; **Source of truth:** Audit report or written text / approval; **OP ammount:** 35000; **Milestone Type:** Critical; **OP tokens request:** User incentives 40% upfront; **Cycle:** Cycle 26; **Completed:** Not Completed; **OP deployment date:** Dec 8; **Incentives due date:** Dec 8
