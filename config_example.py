#!/usr/bin/env python3
"""
Example configurations for different network scenarios
"""

from fraud_detection import FraudDetection

def small_dense_network():
    """Small network with high connectivity"""
    return FraudDetection(
        N=10,
        p_comm=0.6,
        p_trust=0.4, 
        p_noise=0.02,
        cluster_strength=0.9
    )

def large_sparse_network():
    """Large network with low connectivity"""
    return FraudDetection(
        N=50,
        p_comm=0.1,
        p_trust=0.05,
        p_noise=0.15,
        cluster_strength=0.3
    )

def realistic_network():
    """Realistic fraud detection scenario"""
    return FraudDetection(
        N=25,
        p_comm=0.2,
        p_trust=0.1,
        p_noise=0.08,
        cluster_strength=0.7
    )

if __name__ == "__main__":
    # Test different configurations
    configs = {
        "Small Dense": small_dense_network,
        "Large Sparse": large_sparse_network, 
        "Realistic": realistic_network
    }
    
    for name, config_func in configs.items():
        print(f"\n=== {name} Network ===")
        detector = config_func()
        try:
            detector.clear_database()
            detector.create_fraud_network()
            detector.detect_cliques()
        finally:
            detector.close()
