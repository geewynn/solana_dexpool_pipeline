import json
from pathlib import Path
from typing import Dict, List

from anchorpy import Idl, Program, Provider, Wallet
from solana.rpc.api import Client
from solders.keypair import Keypair


class AnchorRaydiumDecoder:
    """
    Decoder for Raydium AMM V3 accounts on Solana blockchain.

    This class provides functionality to decode various types of Raydium AMM V3 accounts
    including Pool states, Position states (both Personal and Protocol), and TickArray states.
    It uses the Anchor framework for decoding account data based on the Raydium IDL.
    """

    def __init__(self, rpc_url: str):
        """
        Initialize the Raydium AMM V3 decoder.

        Args:
            rpc_url (str): URL of the Solana RPC endpoint
        """
        self.PROGRAM_ID = (
            "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"  # Raydium AMM V3 program ID
        )
        self.rpc_url = rpc_url
        self.program = None  # Will hold the initialized Anchor program

    def initialize(self) -> bool:
        """
        Initialize the Anchor program with the Raydium AMM V3 IDL.

        This method:
        1. Sets up a Solana connection
        2. Creates a dummy wallet (required by Anchor)
        3. Loads the Raydium IDL from file
        4. Initializes the Anchor program

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Set up Solana connection and wallet
            connection = Client(self.rpc_url)
            wallet = Wallet(Keypair())
            provider = Provider(connection, wallet)

            # Load and parse the Raydium IDL
            file_path = Path(__file__).parent / "rayclmmidl.json"
            with open(file_path, "r") as f:
                idl_json = json.load(f)

            # Initialize the Anchor program
            idl = Idl.from_json(json.dumps(idl_json))
            self.program = Program(idl, self.PROGRAM_ID, provider)
            print("Successfully initialized Raydium decoder")
            return True

        except Exception as e:
            print(f"Failed to initialize: {str(e)}")
            return False

    def decode_pool_state(self, decoded) -> Dict:
        """
        Format Pool state account data into a standardized dictionary.

        Args:
            decoded: Raw decoded Pool state account data from Anchor

        Returns:
            Dict: Formatted pool data including:
                - AMM configuration and owner
                - Token mint and vault information
                - Pool parameters (decimals, tick spacing)
                - Liquidity and price data
                - Fee growth and protocol fees
                - Swap amounts and status
                - Reward information
                - Total fees and fund fees
        """
        return {
            "bump": list(decoded.bump),
            "ammConfig": str(decoded.amm_config),
            "owner": str(decoded.owner),
            "tokenMint0": str(decoded.token_mint0),
            "tokenMint1": str(decoded.token_mint1),
            "tokenVault0": str(decoded.token_vault0),
            "tokenVault1": str(decoded.token_vault1),
            "observationKey": str(decoded.observation_key),
            "mintDecimals0": decoded.mint_decimals0,
            "mintDecimals1": decoded.mint_decimals1,
            "tickSpacing": decoded.tick_spacing,
            "liquidity": str(decoded.liquidity),
            "sqrtPriceX64": str(decoded.sqrt_price_x64),
            "tickCurrent": decoded.tick_current,
            "padding3": decoded.padding3,
            "padding4": decoded.padding4,
            "feeGrowthGlobal0X64": str(decoded.fee_growth_global0_x64),
            "feeGrowthGlobal1X64": str(decoded.fee_growth_global1_x64),
            "protocolFeesToken0": str(decoded.protocol_fees_token0),
            "protocolFeesToken1": str(decoded.protocol_fees_token1),
            "swapInAmountToken0": str(decoded.swap_in_amount_token0),
            "swapOutAmountToken1": str(decoded.swap_out_amount_token1),
            "swapInAmountToken1": str(decoded.swap_in_amount_token1),
            "swapOutAmountToken0": str(decoded.swap_out_amount_token0),
            "status": decoded.status,
            "padding": list(decoded.padding),
            "rewardInfos": [
                {
                    "rewardState": reward.reward_state,
                    "openTime": str(reward.open_time),
                    "endTime": str(reward.end_time),
                    "lastUpdateTime": str(reward.last_update_time),
                    "emissionsPerSecondX64": str(reward.emissions_per_second_x64),
                    "rewardTotalEmissioned": str(reward.reward_total_emissioned),
                    "rewardClaimed": str(reward.reward_claimed),
                    "tokenMint": str(reward.token_mint),
                    "tokenVault": str(reward.token_vault),
                    "authority": str(reward.authority),
                    "rewardGrowthGlobalX64": str(reward.reward_growth_global_x64),
                }
                for reward in decoded.reward_infos
            ],
            "tickArrayBitmap": [str(bitmap) for bitmap in decoded.tick_array_bitmap],
            "totalFeesToken0": str(decoded.total_fees_token0),
            "totalFeesClaimedToken0": str(decoded.total_fees_claimed_token0),
            "totalFeesToken1": str(decoded.total_fees_token1),
            "totalFeesClaimedToken1": str(decoded.total_fees_claimed_token1),
            "fundFeesToken0": str(decoded.fund_fees_token0),
            "fundFeesToken1": str(decoded.fund_fees_token1),
            "openTime": str(decoded.open_time),
            "recentEpoch": str(decoded.recent_epoch),
            "padding1": [str(p) for p in decoded.padding1],
            "padding2": [str(p) for p in decoded.padding2],
        }

    def decode_position_state(self, decoded) -> Dict:
        """
        Format Personal Position account data into a standardized dictionary.

        Args:
            decoded: Raw decoded Personal Position account data from Anchor

        Returns:
            Dict: Formatted position data including:
                - NFT mint and pool ID
                - Tick range (upper and lower bounds)
                - Liquidity information
                - Fee growth data
                - Token fees owed
                - Reward information
        """
        return {
            "nftMint": str(decoded.nft_mint),
            "poolId": str(decoded.pool_id),
            "tickLowerIndex": decoded.tick_lower_index,
            "tickUpperIndex": decoded.tick_upper_index,
            "liquidity": str(decoded.liquidity),
            "feeGrowthInside0LastX64": str(decoded.fee_growth_inside0_last_x64),
            "feeGrowthInside1LastX64": str(decoded.fee_growth_inside1_last_x64),
            "tokenFeesOwed0": str(decoded.token_fees_owed0),
            "tokenFeesOwed1": str(decoded.token_fees_owed1),
            "rewardInfos": [
                {
                    "growthInsideLastX64": str(reward.growth_inside_last_x64),
                    "rewardAmountOwed": str(reward.reward_amount_owed),
                }
                for reward in decoded.reward_infos
            ],
        }

    def decode_protocol_position_state(self, decoded) -> Dict:
        """
        Format Protocol Position account data into a standardized dictionary.

        Args:
            decoded: Raw decoded Protocol Position account data from Anchor

        Returns:
            Dict: Formatted protocol position data including:
                - Pool ID
                - Tick range (upper and lower bounds)
                - Liquidity information
                - Fee growth data
                - Token fees owed
                - Reward growth inside information
        """
        return {
            "poolId": str(decoded.pool_id),
            "tickLowerIndex": decoded.tick_lower_index,
            "tickUpperIndex": decoded.tick_upper_index,
            "liquidity": str(decoded.liquidity),
            "feeGrowthInside0LastX64": str(decoded.fee_growth_inside0_last_x64),
            "feeGrowthInside1LastX64": str(decoded.fee_growth_inside1_last_x64),
            "tokenFeesOwed0": str(decoded.token_fees_owed0),
            "tokenFeesOwed1": str(decoded.token_fees_owed1),
            "rewardGrowthInside": [
                str(growth) for growth in decoded.reward_growth_inside
            ],
        }

    def decode_tick_array_state(self, decoded) -> Dict:
        """
        Format TickArray account data into a standardized dictionary.

        Args:
            decoded: Raw decoded TickArray account data from Anchor

        Returns:
            Dict: Formatted tick array data including:
                - Pool ID
                - Starting tick index
                - Array of tick data with:
                    - Initialization status
                    - Tick index
                    - Liquidity information (net and gross)
                    - Fee growth outside data
                    - Reward growth outside data

        Note:
            Includes safety checks for tick initialization and attribute presence
        """
        return {
            "poolId": str(decoded.pool_id),
            "startTickIndex": decoded.start_tick_index,
            "ticks": [
                {
                    "initialized": (
                        tick.initialized if hasattr(tick, "initialized") else False
                    ),
                    "tick": tick.tick,
                    "liquidityNet": str(tick.liquidity_net),
                    "liquidityGross": str(tick.liquidity_gross),
                    "feeGrowthOutside0X64": str(tick.fee_growth_outside0_x64),
                    "feeGrowthOutside1X64": str(tick.fee_growth_outside1_x64),
                    "rewardGrowthsOutsideX64": [
                        str(growth) for growth in tick.reward_growths_outside_x64
                    ],
                }
                for tick in decoded.ticks
                if hasattr(tick, "tick")  # Only include valid ticks
            ],
        }

    def decode_tick_array_bitmap_extension(self, decoded) -> Dict:
        """
        Format TickArrayBitmapExtension account data into a standardized dictionary.
        """
        return {
            "poolId": str(decoded.pool_id),
            "positiveTickArrayBitmap": [
                [str(value) for value in bitmap]
                for bitmap in decoded.positive_tick_array_bitmap
            ],
            "negativeTickArrayBitmap": [
                [str(value) for value in bitmap]
                for bitmap in decoded.negative_tick_array_bitmap
            ],
        }

    def decode_account(self, raw_data: List[int], pubkey: str) -> dict:
        """
        Decode account data and determine its type.

        This method attempts to decode raw account data using the Anchor program
        and formats it based on the detected account type (Pool, Position,
        Protocol Position, or TickArray).

        Args:
            raw_data (List[int]): Raw account data as bytes
            pubkey (str): Public key of the account

        Returns:
            dict: Decoded and formatted account data, or error information if decoding fails.
                Success format:
                {
                    "address": account public key,
                    "parsed": {
                        "name": account type,
                        "data": decoded data,
                        "type": "account"
                    },
                    "program": "raydium_amm_v3",
                    "space": account data size
                }
                Error format:
                {
                    "error": error message
                }
        """
        try:
            # Check if program is initialized
            if not self.program:
                raise Exception("Program not initialized")

            account_data = bytes(raw_data)

            try:
                # Attempt to decode and identify account type
                decoded = self.program.coder.accounts.decode(account_data)
                account_type = type(decoded).__name__

                # Process based on account type
                if account_type == "PoolState":
                    data = self.decode_pool_state(decoded)
                elif account_type == "PersonalPositionState":
                    data = self.decode_position_state(decoded)
                elif account_type == "ProtocolPositionState":
                    data = self.decode_protocol_position_state(decoded)
                elif account_type == "TickArrayState":
                    data = self.decode_tick_array_state(decoded)
                elif account_type == "TickArrayBitmapExtension":
                    data = self.decode_tick_array_bitmap_extension(decoded)
                else:
                    return {"error": f"Unknown account type: {account_type}"}

                # Return formatted data
                return {
                    "address": pubkey,
                    "parsed": {"name": account_type, "data": data, "type": "account"},
                    "program": "raydium_amm_v3",
                    "space": len(account_data),
                }

            except Exception as e:
                print(f"Decode error for {pubkey}: {str(e)}")
                return {"error": f"Failed to decode: {str(e)}"}

        except Exception as e:
            print(f"Error processing account {pubkey}: {str(e)}")
            return {"error": str(e)}
