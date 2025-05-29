# Resolv Labs Security Grant Application

**Project URL:** [Link](https://app.charmverse.io/op-grants/resolv-labs-security-grant-application-5072691667085958)

**Audit Service Provider:**

Sherlock

**Project name:**

Resolv Labs 

**What is this project about?**

Resolv is a protocol maintaining USR, a stablecoin natively backed by Ether (ETH) and pegged to the US Dollar. 

**Project Contact Email:**

resolv@resolv.im 

**Telegram**

@Resolv_Community 

**X handle:**

https://x.com/ResolvLabs 

**Website:**

https://resolv.xyz/ 

**Github:**

https://github.com/resolv-im 

**Demo:**

https://app.resolv.xyz/ 

**Discord/Discourse/Community:**

https://discord.com/invite/HwPhyC4hZt 

**Other:**



**OP request locked:**

13500

**OP request for User incentives:**

31500

**L2 Recipient Address:**

 0x5A973117Dd273676bf4D14313b80562DC8973ba9 

**Distribution plan:**

The incentives will be distributed to security researchers participating in the audit contest based on their performance (number and severity of vulnerabilities found) as well as in the form of fix pay for Lead Senior Watsons. For more information, please refer to the "Watsons" page of our official documentation here: https://docs.sherlock.xyz/audits/watsons

**What is this project going to build?**

1. Why are they going to succeed? Resolv Labs is set for success with its innovative $USR stablecoin, which employs a delta-neutral strategy to protect against market volatility. This design, combined with the founders' extensive fintech and software engineering experience, positions them to effectively meet user needs in the Optimism ecosystem. Since the beta launch 4 months ago TVL has grown to 16m with key integrations and partnerships being completed with companies such as Binance, Deribit, and Hyperliquid. Resolv is trusted by investors such as Delphi Labs, No Limit, Daedalus, Tulipa Capital, Stake DAO and others. 2. Why is what they are going to build novel or valuable to Optimism? Considering the size of the stablecoin market (hundreds of billions $) and Optimism's strong growth potential, an advanced Resolv stablecoin could drive significant user growth and adoption on the chain. 3. How is this project likely to bring and keep new builders to the Optimism ecosystem? By providing a reliable and resilient stablecoin, Resolv Labs will attract new builders seeking dependable financial instruments. The RLP allows developers to implement high-yield strategies without excessive risk, improving engagement within the Optimism community. 4. What are some comparable projects? What differentiates this one? Comparable projects include DAI and USDC, which provide stability but lack advanced risk management. Resolv Labs stands out by using a delta-neutral strategy backed by RLP, allowing $USR to maintain its peg more effectively during market fluctuations. In comparison to other delta-neutral stablecoins - the $USR stablecoin offers a mechanism that enhances stability through a self-balanced protective Resolv Liquidity Pool (RLP). This stability is crucial for users and developers, increasing liquidity and utility within the Optimism DeFi landscape alongside the whole DeFi ecosystem. 5. Service providers: Have you worked on projects similar to this one? Sherlock has audited several projects similar to Resolv, which is a protocol maintaining USR, a stablecoin natively backed by Ether (ETH) and pegged to the US Dollar. These projects include: MakerDAO, which operates the DAI stablecoin, a CDP (collateralized-debt-position) stablecoin backed by various assets. UXD Protocol, a fully collateralized decentralized stablecoin backed by delta-neutral positions using derivatives. TapiocaDAO, offering an Omnichain Money Market and Unstoppable OmniDollar StableCoin, based on LayerZeroV2. Volta, an overcollateralized stablecoin protocol. Unitas Protocol, which creates stablecoins for emerging market currencies. Flat Money, a protocol that allows people to deposit Rocket Pool ETH (rETH) and mint UNIT, a decentralized delta-neutral flatcoin designed to outpace inflation. 6. Will this project be fee-based or free to the end user? At the moment and for the near future there are no plans to take any fees. In a more distant future it is likely that fees are going to be taken from the yield of the whole protocol. 7. Will this project be open-source? Yes, Resolv Labs aims for all smart contracts to be open-source, promoting transparency and trust within the Optimism ecosystem.

**Who are the founders? please cover:**

What makes them well-positioned to accomplish your project goals? The founding team of Resolv Labs consists of Ivan Kozlov, Tim Shekikhachev, and Fedor Chmilev. Their diverse backgrounds in technology, finance, and software engineering uniquely position them to achieve the project goals centered around the development of the stablecoin $USR. Ivan Kozlov (CEO) has a strong foundation in digital assets and fintech (spent around a decade in TradFi and with crypto products), which equips him with the necessary skills to lead Resolv Labs in navigating the complexities of the cryptocurrency market. Tim Shekikhachev (CPO) brings extensive knowledge in product development and management within the tech sector, particularly in adapting general and traditional financials for broader use with blockchain technologies. Fedor Chmilev (CTO) has over a decade of experience as a software engineer, previously leading engineering teams at Revolut in their crypto and trading divisions. Is this their first Web3 project? No, this is not their first Web3 project. Fedor Chmilev, as noted, has substantial experience from his tenure at Revolut, contributing to their crypto offerings. He also previously created a no-code Web3 to Web2 integration platform (https://atomiclinks.webflow.io/) launched on Optimism . Have they worked on anything in the Optimism ecosystem? As noted above, Atomiclinks was launched on Optimism. Overall, the founders' collective experience in fintech, product development, and software engineering positions them well to lead Resolv Labs toward achieving its ambitious goals in the cryptocurrency space.

**Is this project funded?**

Current funding allows the company to operate for up to 12 months. At the moment Resolv Labs doesn’t actively need financial support but potential opportunities are welcomed as there are plans for active fund raise in the near future

**Has this project been the subject of a security breach?**

No.

**Do you anticipate any particular issues or complexity in providing services to this project?**

No.

**Please provide details from your due diligence on this project and audit scope (the due diligence must contain the complexity of the scope, test coverage, and test methodologies applied to the scope)**

The codebase consists of approximately 2,008 nSLOC and includes several important contracts within the contracts directory. Key contracts include: StUSR.sol: Implements the USR stablecoin, handling minting, burning, and rebasing functionalities to maintain the peg to the US Dollar. It likely extends from ERC20RebasingUpgradeable.sol to enable rebasing features. Treasury.sol: Manages the protocol's treasury, handling the collateralization of USR with Ether (ETH). It oversees deposits, withdrawals, and interacts with external connectors to optimize asset management. AaveV3TreasuryConnector.sol: Integrates with Aave V3 to utilize the protocol's lending and borrowing functionalities, enabling the treasury to earn yield on deposited Ether and enhance capital efficiency. LidoTreasuryConnector.sol: Connects the treasury to Lido, allowing the protocol to stake Ether and receive staking rewards, further backing USR with yield-generating assets. ERC20RebasingUpgradeable.sol and ERC20RebasingPermitUpgradeable.sol: Provide base functionalities for rebasing tokens, allowing USR to adjust its total supply to maintain its peg, and supporting permit functionality for gasless approvals. WstUSR.sol: A wrapped, non-rebasing version of USR, enabling compatibility with protocols that do not support rebasing tokens while still representing ownership of USR. RewardDistributor.sol: Manages the distribution of rewards to USR holders, potentially from yield generated by the treasury's activities with Aave, Lido, or other integrated protocols. AddressesWhitelist.sol: Implements access control by maintaining a whitelist of addresses allowed to interact with certain protocol functions, enhancing security and compliance. ExternalRequestsManager.sol, ExternalRequestsManagerBetaV1.sol, and LPExternalRequestsManager.sol: Handle external requests and interactions with other contracts or protocols, managing cross-contract communication and ensuring proper execution flow, especially for liquidity providers. SimpleToken.sol: A basic ERC-20 token contract that may be used for testing, utilities, or representing auxiliary tokens within the protocol. Given the medium complexity of the codebase and our extensive experience with similar stablecoin protocols, the audit is estimated to take around 12 days.

**Optimism alignment**

1. Where is this project currently deployed? Resolv is currently deployed on Ethereum mainnet. We are targeting a full launch of Optimism next, contributing to the ecosystem by bringing our novel stablecoin approach and hopefully generating growth in TVL and users for the Optimism ecosystem. 2. Please order where this project is deployed by TVL or some other relevant metric. We currently have 16m TVL on Ethereum mainnet - DeFi Llama 3. Is the code base to be audited specific to the Optimism deployment? Yes

**What does this audit unlock for the project?**

This audit will unlock the possibility for the project to deploy on Optimism. It also enhances security, strengthening our protocol's defenses, ensuring the protection of user assets, maintaining high safety standards for the protocol as well as the broader Optimism ecosystem. In addition, this audit will increase trust and growth. Demonstrating our robust security practices will foster user confidence and drive broader adoption for Resolv, Optimism, and Web3.

**Client contact point to confirm audit completion:**

@chmilevfa 

## Critical Milestones

- **Title:** Valid list of bugs provided Open; **Source of truth:** Protocol Team / Sherlock official Discord / Sherlock official Twitter; **OP ammount:** ; **Milestone Type:** Critical; **OP tokens request:** ; **Cycle:** Cycle 29; **Completed:** Not Completed; **OP deployment date:** ; **Incentives due date:** 
