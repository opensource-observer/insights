# Ether.fi OP Mainnet LRT Grant

# Basic Information

- **Project Name:** Clusters.xyz
- **Project Url:** https://app.charmverse.io/op-grants/clusters-xyz-7959150966012731

## Contact Info

- **Email:** Clusters.xyz
- **Telegram:** Clusters is a universal name service where a user’s identity follows them no matter which chain or L2 they’re on. People don’t sign their name differently based on geography or language, so why should it be any different in crypto?
- **X handle:** foobar@delegate.xyz
- **Discord/Discourse/Community:** @foobar0x
- **Demo:** https://x.com/clustersxyz
- **Other:** https://clusters.xyz/

# Grant Request

- **OP request Locked:** 0
- **OP request for User Incentives:** 35000
- **L2 Recipient Address:** 
    - **:** https://github.com/clustersxyz
- **Please briefly explain how we will be able to confirm that the OP has been spent:** N/A

# Project Details

- **If this is a resubmission from a declined Application, please provide the link to the previous Application, and briefly explain the main areas of improvement. If not please write (N/A):** 1. Why are they going to succeed? Clusters is a universal name service solving two core problems: (1) squatting; (2) wallet bundling. Existing name services like ENS and Basenames are powerful solutions, but struggle from users having to re-sign up on every new Superchain chain they go to. We allow a user to assign multiple addresses from different chains to a core identity in a single place, removing confusing mental burdens from the users. We’re also rolling out an ecosystem bootstrapping tool that helps users get one-click gas on new chains they configure their cluster with. Why is what they are going to build novel or valuable to Optimism? Optimism’s growth comes heavily from Superchain expansion, dominant players like Base and Worldcoin and even Sony. Clusters is built from the ground up to provide a seamless universal experience across all OPStack chains, fighting fragmentation and improving interoperability. How is this project likely to bring and keep new builders to the Optimism ecosystem? Builders will appreciate working with an identity service that is not only easy to use, but isn’t fragmented across every ecosystem they wish to integrate. What are some comparable projects? What differentiates this one? Comparable projects like Basenames or SpaceID are powerful solutions, but they are stuck in the 1 user = 1 address = 1 chain paradigm, so Clusters aims to augment these protocols by handling address aggregation and cross-L2 interop. Will this project be fee-based or free to the end user? The project is primarily fee-based, although certain core features like wallet bundling will be made available free to the end user. Will this project pay for any portion of the service? Clusters may subsidize or incentive signups depending on how closely we’re working with the target ecosystem. Will this project be open-source? Yes, contracts will be both verified onchain and available in an opensource GitHub repo.
- **Do you have a code audit for your project?:** 1. What makes them well-positioned to accomplish your project goals? 2. Is this their first Web3 project? 3. If not, share links to their other projects (e.g., Github repository). 4. Have they worked on anything in the Optimism ecosystem?
- **Please briefly answer all project details questions:** If so, provide an estimate of how many months of funding runway this project has. If there is an active need for financial support, please outline.

# Market Analysis:

- **Please briefly answer all market analysis questions:** Please describe if so and any mitigation measures taken.

# Grant's impact

- **Please briefly answer all grant's impact questions:** No
- **Full list of the project’s labeled contracts:** Audit Scope: will be open sourced codebase: https://github.com/clustersxyz/clusters Testing: Clusters has fuzzing and unit tests. They will have 100% test coverage by the audit. Overview of scope: Complexity: Cross chain name registry allowing association of multiple wallet addresses under a single name. Has mechanisms to prevent name squating, pretty interesting. Uses layerzero for cross-chain messaging. - namemanagerhub.sol - manages the name service function, bidding/buying/tranferring names, along with pricing and banking of them - endpoint.sol - handles cross-chain comms via LZ, send/receives messages between different networks - clustershub.sol - extends namemanagerHub and adds cluster-specific functions, so creation/verification/deletion of clustors, and addition/removal within them as well. - enurablesetlib.sol set operations for bytes32 values - pricingharberger.sol implements harberger tax pricing model for the name service - pricingflat.sol - alternate pricing model that uses flat rate instead of harberger tax model - basicUUPSImpl - proxy upgrade standard and everything else in /interfaces/ Given the nature of the codebase, in terms of nloc, complexity of code and skills required the best solution would be to leverage a Cantina security competition. This project will be fully open source and a Cantina competition will align with open source ethos of this project. Competition details: We can be flexible on how we can structure the competition in terms of rewards, Clusters is also looking to pay the rest of the total cost that is not covered by the OP subsidy. We would structure the competition with a rewards pot of with 32,051 OP with 16,025 OP for the administration, facilitation and judging feeof the competition. We are looking to be subsidised by the OP grant of 35,000 OP tokens to cover a portion of the total cost of 48,076 - Clusters.xyz will be able to pay the surplus amount (13,076 OP) of the total cost not covered by the OP Grant. We do not anticipate needing any extensions, but if we encounter anything that would indicate the need for extensions we will inform the client immediately. A fix review period at the end of the competition will be handled and picked from the top performers of the competition and this review period will be scoped based exactly on the fixes/remediations created as a separate engagement which we will notify OP security council on the associated cost.

# Metrics improved by OP incentives

- **Select the metric specified in the mission request:** Spearbit/Cantina
- **Fill out your metric objective:** N/A

# Budget and Plan

- **Please briefly answer all budget and plan questions:** Hey, It seems the requested OP amount is a bit too big for the scoped work. Let us know if you can work something out.

# Optimism relationship

- **Please briefly answer all Optimism relationship questions:** Please provide into the github link, the link to the scoped contracts. Also please provide the name of the scoped contracts/directories in the due diligence field

# External Contributions:

- **Use of Grant-as-a-service provider:** N/A
- **Contributions from non-team members:** 0xB6B9E9e56AB5a4AF927faa802ac93786352f3af9

# Compliance and Policies

- **Confirm understanding of clawback and milestone requirements:** Critical
- **Confirmation of understanding grant policies:** User incentives 40% upfront
- **KYC information requirement:** Cycle 26
- **Certification of legal compliance for token distribution:** Not Completed

# Milestones

- **Critical milestones for project execution:**     - {'milestone_type': 'Audits application', 'op_tokens_request': 'Audit and Special Mission reviewers', 'cycle': 'Council', 'completed': 'N/A', 'title': 'Audit Completion (report or written approval by Clusters Team)', 'source_of_truth': 'Audit report or written text / approval', 'op_amount': '35000', 'op_deployment_date': 'Dec 8', 'incentives_due_date': 'Dec 8'}
