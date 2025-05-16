def serialize_whirlpool_reward_info(reward_info):
    return {
        "mint": str(reward_info.mint),
        "vault": str(reward_info.vault),
        "authority": str(reward_info.authority),
        "emissions_per_second_x64": str(reward_info.emissions_per_second_x64),
        "growth_global_x64": str(reward_info.growth_global_x64),
    }


def serialize_token_accounts(token_accounts):
    return {
        "mint": str(token_accounts.mint),
        "owner": str(token_accounts.owner),
        "amount": str(token_accounts.amount),
        "delegate": str(token_accounts.delegate),
        "is_native": token_accounts.is_native,
        "delegated_amount": str(token_accounts.delegated_amount),
        "close_authority": str(token_accounts.close_authority),
    }


def serialize_whirlpool(whirlpool, whirlpool_pubkey, token):
    return {
        "pubkey": str(whirlpool_pubkey),
        "token": token,
        "whirlpools_config": str(whirlpool.whirlpools_config),
        "whirlpool_bump": [int(b) for b in whirlpool.whirlpool_bump],
        "tick_spacing": whirlpool.tick_spacing,
        "tick_spacing_seed": [int(s) for s in whirlpool.tick_spacing_seed],
        "fee_rate": whirlpool.fee_rate,
        "protocol_fee_rate": whirlpool.protocol_fee_rate,
        "liquidity": str(whirlpool.liquidity),
        "sqrt_price": str(whirlpool.sqrt_price),
        "tick_current_index": whirlpool.tick_current_index,
        "protocol_fee_owed_a": str(whirlpool.protocol_fee_owed_a),
        "protocol_fee_owed_b": str(whirlpool.protocol_fee_owed_b),
        "token_mint_a": str(whirlpool.token_mint_a),
        "token_vault_a": str(whirlpool.token_vault_a),
        "fee_growth_global_a": str(whirlpool.fee_growth_global_a),
        "token_mint_b": str(whirlpool.token_mint_b),
        "token_vault_b": str(whirlpool.token_vault_b),
        "fee_growth_global_b": str(whirlpool.fee_growth_global_b),
        "reward_last_updated_timestamp": whirlpool.reward_last_updated_timestamp,
        "reward_infos": [
            serialize_whirlpool_reward_info(ri) for ri in whirlpool.reward_infos
        ],
    }


def serialize_tick_array(tick_array):
    return {
        "pubkey": str(tick_array.pubkey),
        "start_tick_index": tick_array.start_tick_index,
        "ticks": [
            {
                "initialized": tick.initialized,
                "liquidity_net": str(tick.liquidity_net),
                "liquidity_gross": str(tick.liquidity_gross),
                "fee_growth_outside_a": str(tick.fee_growth_outside_a),
                "fee_growth_outside_b": str(tick.fee_growth_outside_b),
                "reward_growths_outside": [str(g) for g in tick.reward_growths_outside],
            }
            for tick in tick_array.ticks
        ],
        "whirlpool": str(tick_array.whirlpool),
    }


def serialize_position_bundle(bundle):
    if bundle is None:
        return None
    return {
        "pubkey": str(bundle.pubkey),
        "position_bundle_mint": str(bundle.position_bundle_mint),
        "position_bitmap": [int(b) for b in bundle.position_bitmap],
    }


def serialize_position_reward_info(ri):
    return {
        "growth_inside_checkpoint": str(ri.growth_inside_checkpoint),
        "amount_owed": str(ri.amount_owed),
    }


def serialize_position(pos):
    if pos is None:
        return None
    return {
        "pubkey": str(pos.pubkey),
        "whirlpool": str(pos.whirlpool),
        "position_mint": str(pos.position_mint),
        "liquidity": str(pos.liquidity),
        "tick_lower_index": pos.tick_lower_index,
        "tick_upper_index": pos.tick_upper_index,
        "fee_growth_ckpt_a": str(pos.fee_growth_checkpoint_a),
        "fee_owed_a": str(pos.fee_owed_a),
        "fee_growth_ckpt_b": str(pos.fee_growth_checkpoint_b),
        "fee_owed_b": str(pos.fee_owed_b),
        "reward_infos": [serialize_position_reward_info(ri) for ri in pos.reward_infos],
    }
