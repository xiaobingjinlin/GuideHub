"""
分发糖果 —— 与教程代码中的 Solution.candy 对齐。
"""

from __future__ import annotations


class Solution:
    def candy(self, ratings: list[int]) -> int:
        """两次贪心扫描求最少发糖数。"""
        n = len(ratings)
        candies = [1] * n

        for i in range(1, n):
            if ratings[i] > ratings[i - 1]:
                candies[i] = candies[i - 1] + 1

        for i in range(n - 2, -1, -1):
            if ratings[i] > ratings[i + 1]:
                candies[i] = max(candies[i], candies[i + 1] + 1)

        return sum(candies)

    def candy_detail(self, ratings: list[int]) -> dict:
        """额外返回左右扫过程，方便前端演示。"""
        n = len(ratings)
        candies = [1] * n
        logs: list[str] = [f"样例 ratings = {ratings}", "初始化：每人 1 颗糖"]

        for i in range(1, n):
            if ratings[i] > ratings[i - 1]:
                candies[i] = candies[i - 1] + 1
                logs.append(
                    f"左→右 i={i}：rating {ratings[i]} > 左邻 {ratings[i - 1]} ⇒ candies[{i}]={candies[i]}"
                )
        left_pass = list(candies)
        logs.append(f"左扫结束：{left_pass}")

        for i in range(n - 2, -1, -1):
            if ratings[i] > ratings[i + 1]:
                nxt = max(candies[i], candies[i + 1] + 1)
                if nxt != candies[i]:
                    logs.append(
                        f"右→左 i={i}：rating {ratings[i]} > 右邻 {ratings[i + 1]} "
                        f"⇒ candies[{i}]=max({candies[i]}, {candies[i + 1] + 1})={nxt}"
                    )
                candies[i] = nxt

        total = sum(candies)
        logs.append(f"右扫结束：{candies}")
        logs.append(f"最少糖果总数 = {total}")
        return {
            "ratings": ratings,
            "left_pass": left_pass,
            "candies": candies,
            "total": total,
            "logs": logs,
        }
