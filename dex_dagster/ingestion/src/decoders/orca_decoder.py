import json
from typing import Dict, List

from anchorpy import Idl, Program, Provider, Wallet
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair


class AnchorWhirlpoolDecoder:
    """
    Decoder for Orca Whirlpool accounts on Solana blockchain.

    This class provides functionality to decode various types of Whirlpool accounts
    including the main Whirlpool account, Position accounts, and TickArray accounts.
    It uses the Anchor framework for decoding account data based on the Orca IDL.
    """

    def __init__(self, rpc_url: str):
        """
        Initialize the Whirlpool decoder.

        Args:
            rpc_url (str): URL of the Solana RPC endpoint
        """
        self.PROGRAM_ID = (
            "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"  # Orca Whirlpool program ID
        )
        self.rpc_url = rpc_url
        self.program = None  # Will hold the initialized Anchor program

    def initialize(self) -> bool:
        """
        Initialize the Anchor program with the Whirlpool IDL.

        This method:
        1. Sets up a Solana connection
        2. Creates a dummy wallet (required by Anchor)
        3. Loads the Orca IDL from file
        4. Initializes the Anchor program

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Set up Solana connection and wallet
            connection = AsyncClient(self.rpc_url)
            wallet = Wallet(Keypair())
            provider = Provider(connection, wallet)

            # Load and parse the Orca IDL
            with open("orcaidl.json", "r") as f:
                idl_json = json.load(f)

            # Initialize the Anchor program
            idl = Idl.from_json(json.dumps(idl_json))
            self.program = Program(idl, self.PROGRAM_ID, provider)
            print("Successfully initialized Anchor decoder")
            return True

        except Exception as e:
            print(f"Failed to initialize: {str(e)}")
            return False

    def decode_whirlpool_account(self, decoded) -> Dict:
        """
        Format Whirlpool account data into a standardized dictionary.

        Args:
            decoded: Raw decoded Whirlpool account data from Anchor

        Returns:
            Dict: Formatted Whirlpool data including:
                - Pool configuration and parameters
                - Liquidity and price information
                - Token vault details
                - Fee and protocol fee data
                - Reward information
        """
        return {
            "whirlpoolsConfig": str(decoded.whirlpools_config),
            "whirlpoolBump": [decoded.whirlpool_bump],
            "tickSpacing": decoded.tick_spacing,
            "tickSpacingSeed": list(decoded.tick_spacing_seed),
            "feeRate": decoded.fee_rate,
            "protocolFeeRate": decoded.protocol_fee_rate,
            "liquidity": str(decoded.liquidity),
            "sqrtPrice": str(decoded.sqrt_price),
            "tickCurrentIndex": decoded.tick_current_index,
            "protocolFeeOwedA": str(decoded.protocol_fee_owed_a),
            "protocolFeeOwedB": str(decoded.protocol_fee_owed_b),
            "tokenMintA": str(decoded.token_mint_a),
            "tokenVaultA": str(decoded.token_vault_a),
            "feeGrowthGlobalA": str(decoded.fee_growth_global_a),
            "tokenMintB": str(decoded.token_mint_b),
            "tokenVaultB": str(decoded.token_vault_b),
            "feeGrowthGlobalB": str(decoded.fee_growth_global_b),
            "rewardLastUpdatedTimestamp": str(decoded.reward_last_updated_timestamp),
            "rewardInfos": [
                {
                    "mint": str(reward.mint),
                    "vault": str(reward.vault),
                    "authority": str(reward.authority),
                    "emissionsPerSecondX64": str(reward.emissions_per_second_x64),
                    "growthGlobalX64": str(reward.growth_global_x64),
                }
                for reward in decoded.reward_infos
            ],
        }

    def decode_position_account(self, decoded) -> Dict:
        """
        Format Position account data into a standardized dictionary.

        Args:
            decoded: Raw decoded Position account data from Anchor

        Returns:
            Dict: Formatted Position data including:
                - Associated Whirlpool and position mint
                - Liquidity information
                - Tick range (upper and lower bounds)
                - Fee growth checkpoints and owed fees
                - Reward information
        """
        return {
            "whirlpool": str(decoded.whirlpool),
            "positionMint": str(decoded.position_mint),
            "liquidity": str(decoded.liquidity),
            "tickLowerIndex": decoded.tick_lower_index,
            "tickUpperIndex": decoded.tick_upper_index,
            "feeGrowthCheckpointA": str(decoded.fee_growth_checkpoint_a),
            "feeOwedA": str(decoded.fee_owed_a),
            "feeGrowthCheckpointB": str(decoded.fee_growth_checkpoint_b),
            "feeOwedB": str(decoded.fee_owed_b),
            "rewardInfos": [
                {
                    "growthInsideCheckpoint": str(reward.growth_inside_checkpoint),
                    "amountOwed": str(reward.amount_owed),
                }
                for reward in decoded.reward_infos
            ],
        }

    def decode_tick_array_account(self, decoded) -> Dict:
        """
        Format TickArray account data into a standardized dictionary.

        Args:
            decoded: Raw decoded TickArray account data from Anchor

        Returns:
            Dict: Formatted TickArray data including:
                - Starting tick index
                - Array of tick data (liquidity, fees, rewards)
                - Associated Whirlpool
        """
        return {
            "startTickIndex": decoded.start_tick_index,
            "ticks": [
                {
                    "initialized": tick.initialized,
                    "liquidityNet": str(tick.liquidity_net),
                    "liquidityGross": str(tick.liquidity_gross),
                    "feeGrowthOutsideA": str(tick.fee_growth_outside_a),
                    "feeGrowthOutsideB": str(tick.fee_growth_outside_b),
                    "rewardGrowthsOutside": [
                        str(growth) for growth in tick.reward_growths_outside
                    ],
                }
                for tick in decoded.ticks
            ],
            "whirlpool": str(decoded.whirlpool),
        }

    def decode_account(self, raw_data: List[int], pubkey: str) -> dict:
        """
        Decode account data and determine its type.

        This method attempts to decode raw account data using the Anchor program
        and formats it based on the detected account type (Whirlpool, Position,
        or TickArray).

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
                    "program": "whirlpool",
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
                if account_type == "Whirlpool":
                    data = self.decode_whirlpool_account(decoded)
                elif account_type == "Position":
                    data = self.decode_position_account(decoded)
                elif account_type == "TickArray":
                    data = self.decode_tick_array_account(decoded)
                else:
                    return {"error": f"Unknown account type: {account_type}"}

                # Return formatted data
                return {
                    "address": pubkey,
                    "parsed": {"name": account_type, "data": data, "type": "account"},
                    "program": "whirlpool",
                    "space": len(account_data),
                }

            except Exception as e:
                print(f"Decode error for {pubkey}: {str(e)}")
                return {"error": f"Failed to decode: {str(e)}"}

        except Exception as e:
            print(f"Error processing account {pubkey}: {str(e)}")
            return {"error": str(e)}
